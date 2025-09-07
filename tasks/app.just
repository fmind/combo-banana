# run app tasks
[group('app')]
app: app-run

# run the app live
[group('app')]
app-run:
    uv run gradio app.py
