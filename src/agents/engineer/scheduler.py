# -*- coding: utf-8 -*-
"""
Scheduler - Agendamento de Execuções

Responsável por:
- Agendar execuções periódicas do pipeline
- Definir frequência por entidade
- Controlar horários de execução
- Gerar logs de execução

NOTA: Para produção, recomenda-se usar:
- Azure Functions (Timer Trigger)
- Azure Data Factory
- Cron (Linux) ou Task Scheduler (Windows)
"""

import logging
import time
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from threading import Thread, Event

from .orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Agendador de execuções do pipeline ETL.

    Exemplo de uso:
        scheduler = Scheduler()

        # Agendar execução diária às 6h
        scheduler.schedule_daily(hour=6, entities=["clientes", "produtos"])

        # Agendar execução a cada hora
        scheduler.schedule_interval(hours=1, entities=["estoque"])

        # Iniciar scheduler
        scheduler.start()

        # Parar scheduler
        scheduler.stop()

    Para produção, use este scheduler apenas para testes locais.
    Em ambiente de produção, use Azure Functions ou cron.
    """

    # Configuração padrão de frequência por entidade
    DEFAULT_SCHEDULES = {
        "vendedores": {"frequency": "weekly", "day": 0, "hour": 6},  # Segunda 6h
        "clientes": {"frequency": "daily", "hour": 6},
        "produtos": {"frequency": "daily", "hour": 6, "minute": 15},
        "estoque": {"frequency": "hourly"},
        "vendas": {"frequency": "daily", "hour": 6, "minute": 30}
    }

    def __init__(self, upload_to_cloud: bool = True):
        """
        Inicializa o scheduler.

        Args:
            upload_to_cloud: Fazer upload para Azure Data Lake
        """
        self.upload_to_cloud = upload_to_cloud
        self.orchestrator = Orchestrator(upload_to_cloud=upload_to_cloud)

        self._jobs: List[Dict[str, Any]] = []
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._running = False

        self.execution_log: List[Dict[str, Any]] = []

    def schedule_interval(
        self,
        entities: List[str],
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        job_name: Optional[str] = None
    ):
        """
        Agenda execução em intervalos fixos.

        Args:
            entities: Entidades a processar
            hours: Intervalo em horas
            minutes: Intervalo em minutos
            seconds: Intervalo em segundos
            job_name: Nome do job (opcional)
        """
        interval_seconds = hours * 3600 + minutes * 60 + seconds

        if interval_seconds <= 0:
            raise ValueError("Intervalo deve ser maior que zero")

        job = {
            "name": job_name or f"interval_{interval_seconds}s",
            "type": "interval",
            "interval_seconds": interval_seconds,
            "entities": entities,
            "next_run": datetime.now(),
            "last_run": None
        }

        self._jobs.append(job)
        logger.info(f"Job '{job['name']}' agendado: a cada {interval_seconds}s para {entities}")

    def schedule_daily(
        self,
        entities: List[str],
        hour: int = 6,
        minute: int = 0,
        job_name: Optional[str] = None
    ):
        """
        Agenda execução diária em horário fixo.

        Args:
            entities: Entidades a processar
            hour: Hora do dia (0-23)
            minute: Minuto (0-59)
            job_name: Nome do job (opcional)
        """
        job = {
            "name": job_name or f"daily_{hour:02d}{minute:02d}",
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "entities": entities,
            "next_run": self._calculate_next_daily(hour, minute),
            "last_run": None
        }

        self._jobs.append(job)
        logger.info(f"Job '{job['name']}' agendado: diário às {hour:02d}:{minute:02d} para {entities}")

    def schedule_weekly(
        self,
        entities: List[str],
        day: int = 0,
        hour: int = 6,
        minute: int = 0,
        job_name: Optional[str] = None
    ):
        """
        Agenda execução semanal.

        Args:
            entities: Entidades a processar
            day: Dia da semana (0=Segunda, 6=Domingo)
            hour: Hora do dia (0-23)
            minute: Minuto (0-59)
            job_name: Nome do job (opcional)
        """
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

        job = {
            "name": job_name or f"weekly_{days[day]}_{hour:02d}{minute:02d}",
            "type": "weekly",
            "day": day,
            "hour": hour,
            "minute": minute,
            "entities": entities,
            "next_run": self._calculate_next_weekly(day, hour, minute),
            "last_run": None
        }

        self._jobs.append(job)
        logger.info(f"Job '{job['name']}' agendado: {days[day]} às {hour:02d}:{minute:02d} para {entities}")

    def _calculate_next_daily(self, hour: int, minute: int) -> datetime:
        """Calcula próxima execução diária."""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    def _calculate_next_weekly(self, day: int, hour: int, minute: int) -> datetime:
        """Calcula próxima execução semanal."""
        now = datetime.now()
        days_ahead = day - now.weekday()

        if days_ahead < 0:
            days_ahead += 7

        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(weeks=1)

        return next_run

    def start(self, blocking: bool = True):
        """
        Inicia o scheduler.

        Args:
            blocking: Se True, bloqueia o thread principal
        """
        if self._running:
            logger.warning("Scheduler já está rodando")
            return

        if not self._jobs:
            logger.warning("Nenhum job agendado")
            return

        self._running = True
        self._stop_event.clear()

        logger.info(f"Iniciando scheduler com {len(self._jobs)} jobs...")

        if blocking:
            self._run_loop()
        else:
            self._thread = Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Para o scheduler."""
        if not self._running:
            return

        logger.info("Parando scheduler...")
        self._stop_event.set()
        self._running = False

        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self):
        """Loop principal do scheduler."""
        while not self._stop_event.is_set():
            now = datetime.now()

            for job in self._jobs:
                if job["next_run"] <= now:
                    self._execute_job(job)
                    self._update_next_run(job)

            # Verificar a cada 10 segundos
            self._stop_event.wait(10)

    def _execute_job(self, job: Dict[str, Any]):
        """Executa um job."""
        logger.info(f"Executando job '{job['name']}'...")

        start_time = datetime.now()

        try:
            results = self.orchestrator.run_pipeline(entities=job["entities"])

            execution = {
                "job": job["name"],
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "success": all(r.get("success") for r in results.values()),
                "entities": job["entities"],
                "results": results
            }

        except Exception as e:
            logger.error(f"Erro no job '{job['name']}': {e}")
            execution = {
                "job": job["name"],
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

        job["last_run"] = datetime.now()
        self.execution_log.append(execution)

    def _update_next_run(self, job: Dict[str, Any]):
        """Atualiza próxima execução de um job."""
        if job["type"] == "interval":
            job["next_run"] = datetime.now() + timedelta(seconds=job["interval_seconds"])

        elif job["type"] == "daily":
            job["next_run"] = self._calculate_next_daily(job["hour"], job["minute"])

        elif job["type"] == "weekly":
            job["next_run"] = self._calculate_next_weekly(job["day"], job["hour"], job["minute"])

    def run_once(self, entities: Optional[List[str]] = None):
        """
        Executa o pipeline uma vez (sem agendamento).

        Args:
            entities: Entidades a processar (None = todas)
        """
        if entities:
            return self.orchestrator.run_pipeline(entities=entities)
        else:
            return self.orchestrator.run_full_pipeline()

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do scheduler."""
        return {
            "running": self._running,
            "jobs": [
                {
                    "name": j["name"],
                    "type": j["type"],
                    "entities": j["entities"],
                    "next_run": j["next_run"].isoformat() if j["next_run"] else None,
                    "last_run": j["last_run"].isoformat() if j["last_run"] else None
                }
                for j in self._jobs
            ],
            "execution_count": len(self.execution_log)
        }

    def get_execution_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna log de execuções recentes."""
        return self.execution_log[-limit:]


# Entry point para execução via linha de comando
def main():
    """Executa o scheduler via CLI."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Scheduler do Agente Engenheiro")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Executar uma vez e sair"
    )
    parser.add_argument(
        "--entities",
        nargs="+",
        help="Entidades a processar"
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Intervalo em minutos para execução periódica"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Não fazer upload para Azure"
    )

    args = parser.parse_args()

    scheduler = Scheduler(upload_to_cloud=not args.no_upload)

    if args.run_once:
        # Execução única
        scheduler.run_once(entities=args.entities)
    else:
        # Execução periódica
        entities = args.entities or list(Orchestrator.ENTITIES.keys())
        interval = args.interval or 60

        scheduler.schedule_interval(
            entities=entities,
            minutes=interval,
            job_name="main_pipeline"
        )

        print(f"Scheduler iniciado. Executando a cada {interval} minutos.")
        print("Pressione Ctrl+C para parar.")

        try:
            scheduler.start(blocking=True)
        except KeyboardInterrupt:
            scheduler.stop()
            print("\nScheduler parado.")


if __name__ == "__main__":
    main()
