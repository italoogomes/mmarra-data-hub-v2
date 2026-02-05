# 🚀 Como usar a Collection do Postman

## 1️⃣ Importar no Postman

1. Abra o Postman
2. Clique em **Import** (canto superior esquerdo)
3. Arraste o arquivo `Nexus-Sankhya-Compras.postman_collection.json`
4. Pronto!

---

## 2️⃣ Configurar suas credenciais

1. Clique na Collection **"MMarra Data Hub - Compras"**
2. Vá na aba **Variables**
3. Altere:
   - `base_url` → URL do seu Sankhya (ex: `https://mmarra.sankhya.com.br`)
4. Na request de **Login**, altere o body:
   - `SEU_USUARIO` → seu usuário
   - `SUA_SENHA` → sua senha

---

## 3️⃣ Ordem de execução

```
1. 01. Auth > Login              ← Faz isso primeiro!
   (o token é salvo automaticamente)

2. 02. Explorar Pedido 1167452   ← Testa com o pedido que você tem
   - 2.1 Cabeçalho
   - 2.2 Itens
   - 2.3 Fornecedor
   - 2.4 Tipo de Operação
   - 2.5 Produtos

3. 03. Descobrir Estrutura       ← Entender os campos
   - 3.1 Colunas da TGFCAB
   - 3.2 Colunas da TGFITE
   - 3.3 Tipos de Operação
   - 3.4 Status possíveis

4. 04. Pendências de Compras     ← Relatório que queremos
   - 4.1 Pedidos pendentes
   - 4.2 Resumo por status
   - 4.3 Resumo por fornecedor
   - 4.4 Pedidos atrasados
```

---

## 4️⃣ O que já sabemos

### Tipos de Operação de Compra
| Código | Descrição |
|--------|-----------|
| `1001` | Compra para Estoque |
| `1301` | Compra Casada |

### Tabelas principais
| Tabela | Conteúdo |
|--------|----------|
| `TGFCAB` | Cabeçalho dos pedidos/notas |
| `TGFITE` | Itens dos pedidos |
| `TGFPAR` | Parceiros (fornecedores) |
| `TGFPRO` | Produtos |
| `TGFTOP` | Tipos de operação |

### Campos importantes (provável)
| Campo | Tabela | Descrição |
|-------|--------|-----------|
| `NUNOTA` | TGFCAB | Número único (PK) |
| `NUMNOTA` | TGFCAB | Número da nota/pedido |
| `DTNEG` | TGFCAB | Data da negociação |
| `DTPREVENT` | TGFCAB | Data prevista entrega |
| `CODPARC` | TGFCAB | Código do fornecedor |
| `CODTIPOPER` | TGFCAB | Tipo de operação |
| `VLRNOTA` | TGFCAB | Valor total |
| `STATUSNOTA` | TGFCAB | Status do pedido |
| `CODEMP` | TGFCAB | Empresa/filial |

---

## 5️⃣ Dúvidas a descobrir

Quando rodar as queries, anota:

- [ ] Quais valores de `STATUSNOTA` significam "pendente"?
- [ ] Tem campo de `DTENTRADA` (data real de entrada)?
- [ ] Tem campo de observação/justificativa?
- [ ] Quais campos `AD_*` customizados existem?
- [ ] Tem outros tipos de operação além de 1001 e 1301?

---

## 💡 Dica

Depois de rodar as queries, me manda os resultados que a gente monta o relatório de pendências juntos! 🚀
