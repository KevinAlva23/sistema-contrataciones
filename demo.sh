#!/bin/bash
# Instancia de demostración con datos ficticios.
# Uso: ./demo.sh            levanta la demo en http://localhost:8081
#      ./demo.sh sembrar    carga candidatos ficticios y la cuenta pública
#      ./demo.sh detener
RED=red-demo
if [ "$1" = "detener" ]; then
  podman rm -f frontend-demo backend-demo; exit 0
fi

if [ "$1" = "sembrar" ]; then
podman exec -i backend-demo python3 - << 'PY'
import os, json, urllib.request, urllib.error
B = "http://localhost:8000"
def call(m, p, d=None, t=None):
    h = {"Content-Type": "application/json"}
    if t: h["Authorization"] = "Bearer " + t
    r = urllib.request.Request(B + p, method=m, headers=h,
                               data=None if d is None else json.dumps(d).encode())
    try: return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e:
        print(p, e.code); return None
tok = call("POST", "/login", {"username": "admin", "password": os.environ["ADMIN_PASSWORD"]})["token"]
datos = [
 ("Ana Pérez","ana@ejemplo.com","Analista","5500000001","contratado"),
 ("Luis Gómez","luis@ejemplo.com","Desarrollador","5500000002","pendiente"),
 ("María Soto","maria@ejemplo.com","Diseñadora","5500000003","pendiente"),
 ("Pedro Ruiz","pedro@ejemplo.com","Analista","5500000004","rechazado"),
 ("Laura Díaz","laura@ejemplo.com","Contadora","5500000005","contratado"),
 ("Carlos Vega","carlos@ejemplo.com","Soporte","5500000006","pendiente"),
]
for n, e, p, t, est in datos:
    c = call("POST", "/candidatos", {"nombre": n, "email": e, "puesto": p, "telefono": t}, tok)
    if c and est != "pendiente":
        call("PATCH", f"/candidatos/{c['id']}?estado={est}", None, tok)
call("POST", "/usuarios", {"username": "demo", "password": "DemoAuditor2026", "rol": "auditor"}, tok)
print("Datos de demostración listos")
PY
exit 0
fi

podman image exists localhost/contrataciones_backend || { echo "Primero ejecuta ./iniciar.sh"; exit 1; }
podman network exists $RED || podman network create $RED
podman volume exists datos-demo || podman volume create datos-demo
podman rm -f frontend-demo backend-demo 2>/dev/null || true

podman run -d --name backend-demo --network $RED --network-alias backend \
  --env-file .env.demo -v datos-demo:/data --read-only --tmpfs /tmp --cap-drop=ALL \
  --security-opt no-new-privileges --memory 256m --pids-limit 100 \
  --restart unless-stopped localhost/contrataciones_backend
for i in $(seq 1 20); do
  podman logs backend-demo 2>&1 | grep -q "Application startup complete" && break
  sleep 1
done
podman run -d --name frontend-demo --network $RED -p 8081:80 \
  --read-only --tmpfs /tmp --tmpfs /var/cache/nginx --tmpfs /var/run \
  --cap-drop=ALL --cap-add=CHOWN --cap-add=SETUID --cap-add=SETGID --cap-add=NET_BIND_SERVICE \
  --security-opt no-new-privileges --memory 128m --pids-limit 100 \
  --restart unless-stopped localhost/contrataciones_frontend
echo "Demo en http://localhost:8081"
