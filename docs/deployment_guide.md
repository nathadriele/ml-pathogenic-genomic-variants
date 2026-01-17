# Deployment Guide - VariantClassifier

Guia completo de deploy do VariantClassifier em diferentes ambientes.

## Sumário

1. [Pré-requisitos](#pré-requisitos)
2. [Deploy Local com Docker Compose](#deploy-local-com-docker-compose)
3. [Deploy em Produção](#deploy-em-produção)
4. [Monitoramento](#monitoramento)
5. [Backup e Recovery](#backup-e-recovery)
6. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

### Sistema Operacional
- Linux (Ubuntu 20.04+ recomendado)
- macOS 10.15+
- Windows 10+ com WSL2

### Hardware Mínimo

**Desenvolvimento:**
- CPU: 2 cores
- RAM: 4 GB
- Disco: 10 GB

**Produção:**
- CPU: 4+ cores
- RAM: 8+ GB
- Disco: 50+ GB SSD

### Software

```bash
# Docker e Docker Compose
docker --version  # >= 20.10
docker-compose --version  # >= 2.0

# Python 3.11+ (para deploy sem Docker)
python --version  # >= 3.11

# Git
git --version
```

---

## Deploy Local com Docker Compose

### 1. Clone o Repositório

```bash
git clone https://github.com/your-org/ml-pathogenic-genomic-variants.git
cd ml-pathogenic-genomic-variants
```

### 2. Configure Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações (opcional)
nano .env
```

**Variáveis importantes:**
- `MODEL_PATH`: Caminho para o modelo treinado
- `API_PORT`: Porta da API (default: 8000)
- `FRONTEND_PORT`: Porta do frontend (default: 8501)
- `LOG_LEVEL`: Nível de log (DEBUG, INFO, WARNING, ERROR)

### 3. Build das Imagens

```bash
# Build da API
docker-compose build api

# Build do Frontend
docker-compose build frontend

# Build de todos os serviços
docker-compose build
```

### 4. Inicie os Serviços

```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 5. Verifique Deploy

```bash
# Health check da API
curl http://localhost:8000/health

# Acesse o frontend
open http://localhost:8501
```

### 6. Parar Serviços

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

---

## Deploy em Produção

### Opção 1: Docker Compose em VPS

#### 1. Prepare o Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
```

#### 2. Configure Firewall

```bash
# Permitir portas 80, 443, 8000, 8501
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 8501/tcp

# Ativar firewall
sudo ufw enable
```

#### 3. Configure Nginx Reverse Proxy

```bash
# Instalar Nginx
sudo apt install nginx -y

# Configurar proxy
sudo nano /etc/nginx/sites-available/variantclassifier
```

**Configuração Nginx:**

```nginx
# API
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Ativar configuração:**

```bash
sudo ln -s /etc/nginx/sites-available/variantclassifier /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Configure SSL com Let's Encrypt

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d api.example.com -d app.example.com

# Auto-renovação
sudo certbot renew --dry-run
```

#### 5. Deploy

```bash
# Copiar arquivos para servidor
scp -r . user@server:/var/www/variantclassifier

# No servidor
cd /var/www/variantclassifier
docker-compose up -d
```

### Opção 2: Kubernetes

#### 1. Criar Deployment YAML

**api-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: variantclassifier-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/variantclassifier-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        env:
        - name: MODEL_PATH
          value: "/app/models/variant_ensemble.joblib"
        volumeMounts:
        - name: models
          mountPath: /app/models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: variantclassifier-api-service
spec:
  selector:
    app: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 2. Deploy no Cluster

```bash
# Aplicar configuração
kubectl apply -f api-deployment.yaml

# Verificar status
kubectl get pods
kubectl get services

# Escalar se necessário
kubectl scale deployment variantclassifier-api --replicas=5
```

### Opção 3: Cloud Services

**AWS ECS:**
1. Push da imagem para ECR
2. Criar task definition
3. Configurar load balancer
4. Deploy com ECS service

**Google Cloud Run:**
```bash
# Build e push
gcloud builds submit --tag gcr.io/PROJECT_ID/variantclassifier-api

# Deploy
gcloud run deploy variantclassifier-api \
  --image gcr.io/PROJECT_ID/variantclassifier-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Azure Container Instances:**
```bash
# Criar resource group
az group create --name variantclassifier-rg --location eastus

# Deploy
az container create \
  --resource-group variantclassifier-rg \
  --name variantclassifier-api \
  --image your-registry/variantclassifier-api:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000
```

---

## Monitoramento

### Logs

```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f frontend

# Kubernetes logs
kubectl logs -f deployment/variantclassifier-api

# Ver logs em arquivo
tail -f logs/api.log
```

### Métricas

**Prometheus + Grafana:**

1. Adicionar exporter ao container
2. Configurar Prometheus para scrape
3. Criar dashboards no Grafana

**Métricas importantes:**
- Requests per second
- Latência (p50, p95, p99)
- Error rate
- CPU e memory usage
- Model prediction distribution

### Health Checks

```bash
# Script de health check
#!/bin/bash
# health_check.sh

API_URL="http://localhost:8000/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $response -eq 200 ]; then
    echo "API healthy"
    exit 0
else
    echo "API unhealthy (status: $response)"
    exit 1
fi
```

**Cron job para health checks:**

```bash
# Adicionar ao crontab
*/5 * * * * /path/to/health_check.sh >> /var/log/health.log 2>&1
```

---

## Backup e Recovery

### Backup do Modelo

```bash
# Script de backup
#!/bin/bash
# backup_model.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/models"
MODEL_PATH="/app/models/variant_ensemble.joblib"

mkdir -p $BACKUP_DIR
cp $MODEL_PATH $BACKUP_DIR/model_$DATE.joblib

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "model_*.joblib" -mtime +7 -delete
```

### Backup dos Dados

```bash
# Backup dos dados de referência
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/external/

# Backup para S3
aws s3 sync data/ s3://variantclassifier-backup/data/
```

### Recovery

```bash
# Recuperar modelo
cp /backups/models/model_20260117_120000.joblib /app/models/variant_ensemble.joblib

# Reiniciar serviço
docker-compose restart api
```

---

## Troubleshooting

### Problema: API não inicia

**Sintoma:** `docker-compose up` falha

**Solução:**
```bash
# Ver logs
docker-compose logs api

# Verificar se modelo existe
ls -lh models/variant_ensemble.joblib

# Rebuild da imagem
docker-compose build --no-cache api
```

### Problema: Erro 504 Gateway Timeout

**Sintoma:** Nginx retorna 504

**Solução:**
```nginx
# Aumentar timeout no nginx
proxy_connect_timeout 300;
proxy_send_timeout 300;
proxy_read_timeout 300;
```

### Problema: Memória insuficiente

**Sintoma:** OOMKilled no Kubernetes

**Solução:**
```yaml
# Aumentar memory limit
resources:
  limits:
    memory: "4Gi"
```

### Problema: Predições lentas

**Sintoma:** Latência > 1 segundo

**Solução:**
```bash
# Escalar horizontalmente
kubectl scale deployment variantclassifier-api --replicas=5

# Otimizar modelo (reduzir n_estimators)
# Usar batch prediction
```

### Problema: Alta CPU

**Sintoma:** CPU constantemente em 100%

**Solução:**
```bash
# Ver número de requests
ab -n 1000 -c 10 http://localhost:8000/health

# Implementar rate limiting
# Aumentar recursos ou escalar
```

---

## Segurança

### Hardening

1. **Rodar como usuário não-root:**
```dockerfile
USER appuser
```

2. **Scan de vulnerabilidades:**
```bash
docker scan variantclassifier-api:latest
```

3. **Atualizar regularmente:**
```bash
docker-compose pull
docker-compose up -d
```

4. **Implementar autenticação:**
- JWT tokens
- API keys
- OAuth2

5. **Rate limiting:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("10/minute")
async def predict():
    ...
```

---

## Performance Tuning

### Otimizações da API

1. **Habilitar cache:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def predict_cached(variant_hash):
    return model.predict(variant)
```

2. **Batch processing:**
```python
# Processar múltiplas variantes de uma vez
predictions = model.predict_proba(X_batch)
```

3. **Async I/O:**
```python
# Usar FastAPI async/await
@app.post("/predict")
async def predict(request: Request):
    # I/O operations
    result = await compute_prediction()
    return result
```

### Otimizações do Modelo

1. **Reduzir tamanho:**
```python
# Menos árvores
xgb_params = {"n_estimators": 100}  # ao invés de 500
```

2. **Quantização:**
```python
# Converter float64 para float32
model = model.astype(np.float32)
```

3. **ONNX export:**
```python
# Exportar para ONNX
onnx_model = convert_to_onnx(model)
```

---

## Checklist de Deploy

**Pré-deploy:**
- [ ] Testes passando
- [ ] Modelo treinado e salvo
- [ ] Variáveis de ambiente configuradas
- [ ] SSL/TLS configurado
- [ ] Firewall configurado
- [ ] Backup strategy definida

**Pós-deploy:**
- [ ] Health check funcionando
- [ ] Logs sendo coletados
- [ ] Métricas sendo monitoradas
- [ ] Alertas configurados
- [ ] Documentação atualizada
- [ ] Time notificado

---

## Suporte

Para questões de deployment:
- Email: ops@example.com
- Slack: #deploy-support
- Documentation: [docs_url]
