# -*- coding: utf-8 -*-
"""
Feriados Brasileiros para Prophet

Gera DataFrame de feriados no formato esperado pelo Prophet.
Inclui feriados fixos e moveis (Carnaval, Pascoa, Corpus Christi).
"""

import logging
from datetime import date, timedelta
from typing import List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BrazilianHolidays:
    """
    Calcula feriados brasileiros para uso com Prophet.

    Inclui:
    - Feriados fixos (Ano Novo, Natal, etc)
    - Feriados moveis (Carnaval, Pascoa, Corpus Christi)
    """

    # Feriados fixos
    FIXED_HOLIDAYS = [
        (1, 1, "Ano Novo"),
        (4, 21, "Tiradentes"),
        (5, 1, "Dia do Trabalho"),
        (9, 7, "Independencia do Brasil"),
        (10, 12, "Nossa Senhora Aparecida"),
        (11, 2, "Finados"),
        (11, 15, "Proclamacao da Republica"),
        (12, 25, "Natal"),
    ]

    def __init__(
        self,
        include_carnival: bool = True,
        include_easter: bool = True,
        include_corpus_christi: bool = True
    ):
        """
        Inicializa o calculador de feriados.

        Args:
            include_carnival: Incluir Carnaval (segunda e terca)
            include_easter: Incluir Sexta-Feira Santa e Pascoa
            include_corpus_christi: Incluir Corpus Christi
        """
        self.include_carnival = include_carnival
        self.include_easter = include_easter
        self.include_corpus_christi = include_corpus_christi

    def get_holidays(
        self,
        start_year: int,
        end_year: int
    ) -> pd.DataFrame:
        """
        Gera DataFrame de feriados no formato Prophet.

        Args:
            start_year: Ano inicial
            end_year: Ano final

        Returns:
            DataFrame com colunas ['ds', 'holiday']
        """
        holidays = []

        for year in range(start_year, end_year + 1):
            # Feriados fixos
            for month, day, name in self.FIXED_HOLIDAYS:
                try:
                    dt = date(year, month, day)
                    holidays.append({"ds": dt, "holiday": name})
                except ValueError:
                    continue

            # Feriados moveis baseados na Pascoa
            easter = self._calculate_easter(year)

            if self.include_easter:
                # Sexta-Feira Santa (2 dias antes da Pascoa)
                good_friday = easter - timedelta(days=2)
                holidays.append({"ds": good_friday, "holiday": "Sexta-Feira Santa"})

                # Pascoa
                holidays.append({"ds": easter, "holiday": "Pascoa"})

            if self.include_carnival:
                # Carnaval (47 dias antes da Pascoa)
                carnival_tuesday = easter - timedelta(days=47)
                carnival_monday = carnival_tuesday - timedelta(days=1)

                holidays.append({"ds": carnival_monday, "holiday": "Segunda de Carnaval"})
                holidays.append({"ds": carnival_tuesday, "holiday": "Terca de Carnaval"})

            if self.include_corpus_christi:
                # Corpus Christi (60 dias apos a Pascoa)
                corpus_christi = easter + timedelta(days=60)
                holidays.append({"ds": corpus_christi, "holiday": "Corpus Christi"})

        # Criar DataFrame
        df = pd.DataFrame(holidays)
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds").reset_index(drop=True)

        return df

    def _calculate_easter(self, year: int) -> date:
        """
        Calcula a data da Pascoa usando o algoritmo de Meeus/Jones/Butcher.

        Args:
            year: Ano

        Returns:
            Data da Pascoa
        """
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        return date(year, month, day)


def get_holidays_dataframe(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years_back: int = 2,
    years_forward: int = 1
) -> pd.DataFrame:
    """
    Funcao de conveniencia para obter feriados.

    Args:
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
        years_back: Anos para tras (se start_date nao especificado)
        years_forward: Anos para frente (se end_date nao especificado)

    Returns:
        DataFrame com feriados
    """
    today = date.today()

    if start_date:
        start_year = pd.to_datetime(start_date).year
    else:
        start_year = today.year - years_back

    if end_date:
        end_year = pd.to_datetime(end_date).year
    else:
        end_year = today.year + years_forward

    holidays = BrazilianHolidays()
    return holidays.get_holidays(start_year, end_year)
