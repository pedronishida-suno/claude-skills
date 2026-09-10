---
name: machine-health-watchdog
description: Checklist de diagnóstico rápido para três problemas recorrentes já mapeados na máquina do Pedro — saturação do microfone interno (ALC257) acima de 30% de boost no PipeWire, pressão de memória resolvida via swap 100% zram + watchdog sysguard, e pipocamento de áudio Bluetooth A2DP em 2.4GHz (fixar codec aptx/aac/sbc_xq). Use quando o pedido for "mic saturando/estourando", "máquina travou/travando", "bluetooth pipocando/cortando", ou qualquer sintoma que bata com esses três padrões já diagnosticados. NÃO use para problemas de hardware/SO novos sem relação com esses três sintomas conhecidos.
---

# /machine-health-watchdog — diagnóstico rápido de problemas recorrentes

## Por que existe

Três causas-raiz já foram diagnosticadas e resolvidas uma vez, mas o sintoma pode reaparecer (nova sessão de áudio, reboot, atualização de firmware/driver) e sem essa skill o diagnóstico começaria do zero.

## Casos conhecidos

1. **Mic interno saturando (ALC257)**: acima de 30% de boost no PipeWire, o boost liga e satura o áudio. Fix: manter o boost em 28%, nunca subir para 30%+.
2. **Travamento por pressão de memória**: causa é pressão de memória sem OOM killer atuando a tempo. Mitigação: swap 100% em zram + watchdog em `~/.local/share/sysguard`. Se travar de novo, primeiro checar se o watchdog está rodando antes de investigar causa nova.
3. **Bluetooth A2DP pipocando em Wi-Fi 2.4GHz**: fones MOMENTUM 4, conflito de aptX HD com a antena Intel CNVi operando em 2.4GHz. Fix: fixar o codec em `aptx`/`aac`/`sbc_xq` (evitar aptX HD nesse cenário) — verificado com zero xrun no PipeWire.

## Passos ao ser acionado

1. Identifique qual dos três sintomas bate com o relato do usuário.
2. Antes de investigar do zero, aplique/verifique o fix já conhecido (boost do mic em 28%, watchdog do sysguard ativo, codec Bluetooth fixado).
3. Só escale para diagnóstico novo se o fix conhecido já estiver aplicado e o sintoma persistir — nesse caso, trate como problema novo, não force o encaixe num dos três casos conhecidos.

## Contexto de referência

Ver memórias locais `mic-interno-boost-satura`, `maquina-memoria-zram-sysguard`, `bluetooth-a2dp-pipoca-24ghz`.
