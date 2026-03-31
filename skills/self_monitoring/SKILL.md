# Self Monitoring Skill

Dieses Skill überwacht den Systemzustand und erweitert das `get_system_status` Tool.

## Erweiterte Funktionen

### Enhanced System Status
Das erweiterte Systemstatus-Tool liefert detaillierte Informationen über:
- CPU: Last, Modell, Kerne
- Speicher: Verwendung in %, MB, GB
- Load Average: 1, 5, 15 Minuten
- GPU: Anzahl, Typ, VRAM (wenn verfügbar)

### Verfügbare Skripte

1. **enhanced_status.py** - Python-Version mit zuverlässiger GPU-Erkennung
2. **enhanced_status_v2.sh** - Bash-Version (experimentell)
3. **extended_system_status.py** - Vollständige Python-Implementierung

## Verwendung

```bash
# Erweiterten Systemstatus abrufen
python3 /ros2_ws/src/bob_central/skills/self_monitoring/enhanced_status.py
```

## GPU-Erkennung

Das Tool erkennt GPUs über:
1. **nvidia-smi** (falls installiert) - Liefert detaillierte VRAM-Informationen
2. **DRM-Schnittstelle** (/sys/class/drm) - Erkennt NVIDIA-GPUs ohne nvidia-smi

## Integration mit get_system_status

Das erweiterte Tool ist kompatibel mit dem bestehenden `get_system_status` Tool, 
erweitert es aber um GPU-Informationen und detailliertere CPU/Speicher-Daten.

## Beispiel-Ausgabe

```json
{
  "cpu": {
    "load_percent": 4.1,
    "model": "13th Gen Intel(R) Core(TM) i9-13900K",
    "cores": 32
  },
  "memory": {
    "used_percent": 11.1,
    "used_mb": 21434,
    "free_mb": 145127,
    "total_mb": 192983,
    "free_gb": 141.73
  },
  "load_average": [1.85, 1.92, 2.01],
  "gpu": {
    "count": 1,
    "info": "NVIDIA GPU (ID: 2684)",
    "total_vram_mb": 0,
    "used_vram_mb": 0,
    "free_vram_mb": 0,
    "details": [
      {
        "name": "NVIDIA GPU (ID: 2684)",
        "vram_total_mb": 0,
        "vram_used_mb": 0,
        "vram_free_mb": 0,
        "detected_via": "DRM"
      }
    ]
  }
}
```