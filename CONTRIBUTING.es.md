# Contribuyendo a GitCrumb

¡Gracias por tu interés en contribuir! Este documento describe cómo participar.

## Requisitos previos

- Python 3.10+
- Git instalado

## Desarrollo local

```bash
git clone git@github.com:<user>/gitcrumb.git
cd gitcrumb
./install.sh
```

## Ejecutar pruebas

```bash
python -m pytest tests/ -v
```

## Enviar cambios

1. Crea una rama desde `main`.
2. Haz tus cambios siguiendo el estilo existente del código.
3. Añade o actualiza las pruebas según corresponda.
4. Ejecuta `pytest` para verificar que todo pasa.
5. Abre un Pull Request describiendo los cambios.

## Pautas de código

- **Solo stdlib**: no se permiten dependencias externas.
- **Python 3.10+**: usa type hints y características modernas del lenguaje.
- **Sin abstracciones innecesarias**: código simple y directo.
- **Pruebas obligatorias**: cada cambio debe estar cubierto por tests.

## Informar un problema

Usa [GitHub Issues](https://github.com/<user>/gitcrumb/issues) para reportar bugs o solicitar mejoras. Incluye:

1. Versión de GitCrumb usada.
2. Sistema operativo y versión de Python.
3. Pasos para reproducir el problema.
4. Comportamiento esperado vs. comportamiento real.
