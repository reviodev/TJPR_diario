FROM python:3.10-slim

WORKDIR /app

# Instalar Chrome e pacotes necessários + cron
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    cron \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código e arquivos de configuração
COPY scraper.py .
COPY .env* .

# Criar diretório para logs e downloads
RUN mkdir -p /app/Diarios /app/logs

# Configurar tarefa cron para executar o scraper todos os dias às 10:00
RUN echo "0 10 * * * cd /app && python /app/scraper.py >> /app/logs/scraper_\$(date +\%Y\%m\%d).log 2>&1" > /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron
RUN crontab /etc/cron.d/scraper-cron

# Criar script de inicialização
COPY <<'EOT' /app/entrypoint.sh
#!/bin/bash
echo "🔄 TJPR Scraper service started"
echo "📅 Cron job scheduled to run at 10:00 AM daily"
service cron start
echo "✅ Cron service started"
echo "📊 Logs will be available at /app/logs/"

# Executar uma vez na inicialização (opcional)
python /app/scraper.py >> /app/logs/scraper_initial.log 2>&1

# Manter o container em execução
tail -f /dev/null
EOT

RUN chmod +x /app/entrypoint.sh

# Usa o script de inicialização em vez de executar diretamente o scraper
CMD ["/app/entrypoint.sh"]