# Control Plane dev2

Flusso reale: controller `intent-create` -> nodo `intent-process` -> controller `result-verify`. Ripetendo lo stesso intent il nodo produce NACK `replay_detected`.

Questa versione non dispone di executor per miner, processi, rete, TEP o configurazioni. L unica action ammessa e `probe.status`.