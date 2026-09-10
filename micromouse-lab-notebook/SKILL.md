---
name: micromouse-lab-notebook
description: Registra e recupera o progresso do projeto micromouse por worktree (controle, PCB, paper) — estado do firmware C, resultado da simulação de controle (cascata+gyro, política CEM), status do KiCad (gerado vs. roteado), e status do paper (short paper para conferência). Use quando o pedido for "log do micromouse", "onde parei no PCB", "status do paper do micromouse", "salva o progresso do micromouse", ou ao retomar trabalho no projeto depois de um tempo parado. NÃO use para dúvidas genéricas de robótica/controle sem relação com o projeto micromouse do Pedro.
---

# /micromouse-lab-notebook — caderno de bordo do projeto micromouse

## Por que existe

O projeto tem três frentes rodando em paralelo dentro do mesmo worktree (controle, PCB, paper) — sem registro estruturado, é fácil perder o fio de qual frente está em qual estado entre sessões, especialmente porque o trabalho não é diário.

## O que registrar/recuperar

1. **Firmware/controle**: linguagem (C), abordagem validada (cascata + gyro, política CEM), resultados de simulação (qual política teve melhor desempenho e por quê).
2. **PCB**: se o layout foi gerado no KiCad e se já foi roteado ou ainda está pendente.
3. **Paper**: alvo de publicação (ex. short paper para conferência), estado do manuscrito (rascunho, submetido, compilando), e problemas de build (ex. LaTeX) já resolvidos, para não re-diagnosticar do zero.
4. **Worktree ativo**: qual branch/worktree concentra o trabalho — checar com `git worktree list` antes de abrir um novo (ver [[fpa-preflight-checklist]] para o princípio geral, aplicado aqui ao contexto pessoal).

## Passos ao ser acionado

1. Ao pedir "status", leia o registro mais recente (memória local ou arquivo de log do projeto) e resuma as três frentes antes de continuar o trabalho.
2. Ao pedir para "salvar progresso", registre o estado atual das três frentes de forma objetiva — o que mudou desde o último registro, o que ficou pendente, e qual é o próximo passo claro em cada frente.
3. Nunca assuma que uma frente parada significa abandonada — sinalize como "pausada" e pergunte se deve retomar antes de descartar contexto.

## Contexto de referência

Ver memória local `micromouse-controle-pcb-paper`.
