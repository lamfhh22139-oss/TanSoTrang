FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pygbag==0.9.2

COPY game.py main.py server.py net.py ./
COPY fonts ./fonts
COPY README.md ./

RUN python -m pygbag --build --title "Tan So Trang" --app_name tansotrang .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
