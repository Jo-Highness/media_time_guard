set -e
pip install --quiet --root-user-action=ignore pytest-homeassistant-custom-component
echo "=== INSTALL DONE ==="
python -c "import homeassistant, sys; print('HA', homeassistant.const.__version__, 'PY', sys.version)"
echo "=== RUNNING PYTEST ==="
pytest -p no:cacheprovider
