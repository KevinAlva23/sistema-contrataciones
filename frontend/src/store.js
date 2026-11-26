import { reactive } from "vue";

export const store = reactive({
  token: sessionStorage.getItem("token") || "",
  usuario: null,
  config: null,
  toast: "",
});

const PERMISOS = {
  edit: ["admin", "reclutador"],
  del: ["admin"],
  apr: ["admin"],
  usuarios: ["admin"],
  aud: ["admin", "auditor"],
};
export const puede = (a) => PERMISOS[a].includes(store.usuario?.rol);

let timer;
export function aviso(msg) {
  store.toast = msg;
  clearTimeout(timer);
  timer = setTimeout(() => (store.toast = ""), 3000);
}

export function guardarToken(t) {
  store.token = t;
  if (t) sessionStorage.setItem("token", t);
  else sessionStorage.removeItem("token");
}

export function salir() {
  guardarToken("");
  store.usuario = null;
}

export async function api(ruta, { metodo = "GET", cuerpo, archivo, blob } = {}) {
  const cab = {};
  if (store.token) cab.Authorization = `Bearer ${store.token}`;
  let body;
  if (archivo) {
    body = new FormData();
    body.append("archivo", archivo);
  } else if (cuerpo !== undefined) {
    cab["Content-Type"] = "application/json";
    body = JSON.stringify(cuerpo);
  }
  let r;
  try {
    r = await fetch(`/api${ruta}`, { method: metodo, headers: cab, body });
  } catch {
    throw new Error("No hay conexión con el servidor");
  }
  if (r.status === 401 && store.token) salir();
  if (!r.ok) {
    const d = await r.json().catch(() => ({}));
    const msg = Array.isArray(d.detail) ? d.detail.map((x) => x.msg).join(". ") : d.detail;
    throw new Error(msg || "Ocurrió un error");
  }
  if (r.status === 204) return null;
  return blob ? r.blob() : r.json();
}

export const fecha = (s) =>
  new Date(s + "Z").toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });
export const dias = (s) => Math.floor((Date.now() - new Date(s + "Z")) / 864e5);
export const NOMBRES = {
  nuevo: "Nuevo",
  revision: "Revisión de CV",
  entrevista: "Entrevista",
  tecnica: "Prueba técnica",
  oferta: "Oferta",
  contratado: "Contratado",
  rechazado: "Rechazado",
};
export const ROLES = { admin: "Administrador", reclutador: "Reclutador", auditor: "Auditor" };
