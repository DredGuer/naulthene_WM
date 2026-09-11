// VIS-01 — la scène 3D du cerveau. Contrat : spec §4 (les trois trames) et §5 (encodage visuel).
//
// ⚠️ CONTRAT DE SONDE (`tests/test_cerveau_3d.py`, classe `TestLogiqueDeLaPage`) : cette page est
// exécutée sous `node` — avec le VRAI `three.core.min.js` vendorisé et un `WebGLRenderer` factice
// — pour vérifier sa LOGIQUE sans navigateur. Les noms `construireStructure`, `appliquerActivite`,
// `construireAretes`, `float16VersFloat32`, `base64EnOctets`, `noeuds`, `aretes` sont donc STABLES :
// les renommer casse la sonde. Le fichier livré, lui, n'exporte rien (un navigateur n'en a pas
// besoin) — la sonde ajoute la ligne `export` à une COPIE temporaire.
//
// ⚠️ Le vendor est LOCAL (`./three.module.js`, v0.180.0 épinglée) : jamais un CDN au runtime.
// Ce fichier-là importe son core `./three.core.min.js` (les classes partagées : `Color`,
// `InstancedMesh`, `Scene`…) — les deux sont servis par `cerveau_3d/serveur.py`.
import * as THREE from './three.module.js';

// --- 1. La scène, la caméra, la lumière ------------------------------------------------------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0b12);
const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.1, 500);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(devicePixelRatio);
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, 0.75));
const lumiere = new THREE.DirectionalLight(0xffffff, 1.1);
lumiere.position.set(6, 9, 8);
scene.add(lumiere);

// Caméra orbitale minimale (pas d'OrbitControls : trois lignes suffisent et évitent un import).
const VUE_OUVERTURE = { theta: 0.8, phi: 1.15, distance: 26 };
const vue = { theta: VUE_OUVERTURE.theta, phi: VUE_OUVERTURE.phi,
              distance: VUE_OUVERTURE.distance, cible: new THREE.Vector3(0, 0, 4) };
let souris = null;
renderer.domElement.addEventListener('pointerdown', e => { souris = { x: e.clientX, y: e.clientY }; });
addEventListener('pointerup', () => { souris = null; });
addEventListener('pointermove', e => {
  if (!souris) return;
  vue.theta -= (e.clientX - souris.x) * 0.006;
  vue.phi = Math.max(0.15, Math.min(Math.PI - 0.15, vue.phi - (e.clientY - souris.y) * 0.006));
  souris = { x: e.clientX, y: e.clientY };
});

// ---------------------------------------------------------------------------------------------
// Le zoom : la MOLETTE et les BOUTONS agissent sur la même grandeur (`vue.distance`) et dans les
// mêmes bornes. Deux réglages séparés divergeraient à la première modification — ici il n'y a
// qu'une fonction, donc un seul comportement à tenir.
//   `+` RAPPROCHE (la distance diminue) · `−` ÉLOIGNE · `⟳` remet la vue d'ouverture.
// ---------------------------------------------------------------------------------------------
const DISTANCE_MIN = 3;
const DISTANCE_MAX = 120;
const PAS_ZOOM = 1.25;

function zoomer(facteur) {
  vue.distance = Math.max(DISTANCE_MIN, Math.min(DISTANCE_MAX, vue.distance * facteur));
}

function recentrer() {
  vue.theta = VUE_OUVERTURE.theta;
  vue.phi = VUE_OUVERTURE.phi;
  vue.distance = VUE_OUVERTURE.distance;
  vue.cible.set(0, 0, 4);
}

renderer.domElement.addEventListener('wheel', e => {
  zoomer(1 + Math.sign(e.deltaY) * 0.1);
}, { passive: true });

function majCamera() {
  camera.position.set(
    vue.cible.x + vue.distance * Math.sin(vue.phi) * Math.cos(vue.theta),
    vue.cible.y + vue.distance * Math.cos(vue.phi),
    vue.cible.z + vue.distance * Math.sin(vue.phi) * Math.sin(vue.theta));
  camera.lookAt(vue.cible);
}

// --- 2. Décodage : les trames transportent du base64 (float16 pour l'activité, int8 pour les
//        poids). Un champ illisible n'est JAMAIS une exception : c'est un champ ABSENT.
function base64EnOctets(texte) {
  if (typeof texte !== 'string' || texte.length === 0) return new Uint8Array(0);
  try {
    return Uint8Array.from(atob(texte), c => c.charCodeAt(0));
  } catch (erreur) {
    return new Uint8Array(0);          // base64 corrompu = champ absent, jamais un écran mort
  }
}

// float16 (petit-boutiste, comme `numpy.tobytes()`) → float32.
//
// ⚠️ On n'appelle PAS `DataView.getFloat16`, pour deux raisons MESURÉES :
//   1. il n'existe pas partout (`undefined` sur Node 22, absent des navigateurs d'avant 2025) :
//      la page tomberait entièrement sur une machine qui l'ignore ;
//   2. son `littleEndian` vaut `false` par DÉFAUT — `getFloat16(offset)` lit en GROS-boutiste
//      alors que numpy écrit en PETIT-boutiste : les neurones seraient placés n'importe où,
//      silencieusement (rien à l'écran ne dirait que le décodage est faux).
// Le décodage pur JS est donc le CHEMIN UNIQUE — et il est testé sur des valeurs extrêmes.
function lireFloat16(octets, position) {
  const bits = octets[position] | (octets[position + 1] << 8);
  const signe = (bits & 0x8000) ? -1 : 1;
  const exposant = (bits >> 10) & 0x1f;
  const mantisse = bits & 0x3ff;
  if (exposant === 0) return signe * mantisse * 5.960464477539063e-8;   // sous-normaux et zéro
  if (exposant === 0x1f) return mantisse ? NaN : signe * Infinity;      // infini ou NaN
  return signe * (1 + mantisse / 1024) * Math.pow(2, exposant - 15);
}

function float16VersFloat32(octets) {
  const nombre = Math.floor(octets.length / 2);
  const sortie = new Float32Array(nombre);
  for (let i = 0; i < nombre; i++) sortie[i] = lireFloat16(octets, i * 2);
  return sortie;
}

// --- 3. L'état de la scène -------------------------------------------------------------------
const noeuds = { maillage: null, couches: [], positions: [], colonne: null, neurones: 0 };
const aretes = { lignes: null, paires: [], horsBornes: 0 };
let seuil = 0.15;

// Le tronc commun (§5) : présent, jamais allumé — la trame d'activité ne porte pas le bus, et on
// ne l'invente pas (spec §9 : « un état inattendu est affiché comme tel, jamais corrigé »).
const COULEUR_COLONNE = [0.10, 0.12, 0.20];

const couleur = new THREE.Color();

// Activation → couleur : du gris sourd (t = 0) au jaune vif (t = 1), §5 de la spec.
// ⚠️ Ruling : une valeur ABSENTE (`null`, un champ manquant, un non-fini) vaut t = 0, donc un
// neurone GRIS — le même gris qu'une activation nulle. On ne devine rien, on ne complète rien.
function couleurActivation(valeur, maximum) {
  const t = Number.isFinite(valeur) && maximum > 0
    ? Math.min(1, Math.max(0, valeur / maximum)) : 0;
  return couleur.setRGB(0.12 + 0.88 * t, 0.12 + 0.72 * t * t, 0.16 + 0.2 * t);
}

function nombre(valeur, defaut) {
  return Number.isFinite(valeur) ? valeur : defaut;
}

// Quelle ENTRÉE d'une couche vient d'un neurone du bus, et quelle entrée vient d'une BORNE (§5 :
// vision 147, audio 130, `vecteur_bio` 44, actions 8 — non neuronales, jamais dessinées) ?
// `bornes` déclare ses intervalles ; le bus latent est le COMPLÉMENT. Rendre `-1` = pas un neurone.
// ⚠️ L'ordre compte : le vecteur bio arrive APRÈS le bus (`cat([pensee, vecteur_bio])`) alors que
// les actions arrivent AVANT (`cat([actions_onehot, pensee])`) — c'est la table qui le dit, jamais
// une supposition de ce fichier.
function planDesEntrees(couche, bornes, dimBus) {
  const entree = Math.max(0, couche.entree | 0);
  const marque = new Uint8Array(entree);            // 1 = entrée NON neuronale (une borne)
  for (const borne of Array.isArray(bornes) ? bornes : []) {
    if (!borne || borne.couche !== couche.nom) continue;
    const intervalle = borne.rang_entree;
    if (!Array.isArray(intervalle) || intervalle.length < 2) continue;
    const debut = Math.max(0, Math.min(entree, Number(intervalle[0]) || 0));
    const fin = Math.max(debut, Math.min(entree, Number(intervalle[1]) || 0));
    for (let i = debut; i < fin; i++) marque[i] = 1;
  }
  const source = new Int32Array(entree).fill(-1);
  let depart = -1;
  for (let i = 0; i <= entree; i++) {
    const estBorne = i < entree ? marque[i] === 1 : true;     // la fin du vecteur ferme le tronçon
    if (!estBorne && depart < 0) depart = i;
    if (estBorne && depart >= 0) {
      for (let k = depart; k < i; k++) source[k] = (k - depart) % dimBus;
      depart = -1;
    }
  }
  return source;
}

// --- 4. La structure : une sphère par neurone (InstancedMesh), plus la colonne du bus ---------
function construireStructure(trame) {
  if (noeuds.maillage) { scene.remove(noeuds.maillage); noeuds.maillage.dispose(); }
  if (aretes.lignes) { scene.remove(aretes.lignes); aretes.lignes.geometry.dispose(); }

  const couches = Array.isArray(trame.couches) ? trame.couches : [];
  const sorties = couches.map(c => Math.max(0, c.sortie | 0));
  const dimBus = Number.isFinite(trame.dim_bus) && trame.dim_bus > 0
    ? Math.floor(trame.dim_bus) : Math.max(1, ...sorties);
  const total = sorties.reduce((n, s) => n + s, 0);
  const geometrie = new THREE.SphereGeometry(0.035, 8, 6);
  const materiau = new THREE.MeshLambertMaterial({ vertexColors: false });
  noeuds.maillage = new THREE.InstancedMesh(geometrie, materiau, total + dimBus);

  const matrice = new THREE.Matrix4();
  const positions = [];
  let index = 0, sansPositions = 0, zMin = Infinity, zMax = -Infinity;
  for (const couche of couches) {
    const points = float16VersFloat32(base64EnOctets(couche.positions));
    const lisible = points.length === Math.max(0, couche.sortie | 0) * 3 ? points : null;
    if (lisible === null) sansPositions++;      // une plaque sans positions est COMPTÉE, pas devinée
    const debut = index;
    for (let i = 0; i < Math.max(0, couche.sortie | 0); i++, index++) {
      const x = lisible ? lisible[i * 3] : 0;
      const y = lisible ? lisible[i * 3 + 1] : 0;
      const z = lisible ? lisible[i * 3 + 2] : 0;
      positions.push([x, y, z]);
      matrice.makeTranslation(x, y, z);
      noeuds.maillage.setMatrixAt(index, matrice);
      noeuds.maillage.setColorAt(index, couleurActivation(0, 1));
      if (lisible) { zMin = Math.min(zMin, z); zMax = Math.max(zMax, z); }
    }
    couche._debut = debut;
    couche._source = planDesEntrees(couche, trame.bornes, dimBus);
  }

  // La colonne du bus latent, AU CENTRE (§5) : `dim_bus` neurones répartis sur la profondeur des
  // plaques — le tronc commun que toutes les couches consomment.
  const colonne = { debut: index, taille: dimBus };
  const profondeur = Number.isFinite(zMin) && Number.isFinite(zMax);
  for (let k = 0; k < dimBus; k++, index++) {
    const part = dimBus > 1 ? k / (dimBus - 1) : 0.5;
    const z = profondeur ? zMin + (zMax - zMin) * part : 0;
    positions.push([0, 0, z]);
    matrice.makeTranslation(0, 0, z);
    noeuds.maillage.setMatrixAt(index, matrice);
    noeuds.maillage.setColorAt(index, couleur.setRGB(COULEUR_COLONNE[0], COULEUR_COLONNE[1],
                                                     COULEUR_COLONNE[2]));
  }

  noeuds.couches = couches;
  noeuds.positions = positions;
  noeuds.colonne = colonne;
  noeuds.neurones = total;
  noeuds.sansPositions = sansPositions;
  noeuds.maillage.instanceMatrix.needsUpdate = true;
  noeuds.maillage.instanceColor.needsUpdate = true;
  scene.add(noeuds.maillage);

  const niveau = (trame.niveau && trame.niveau.affiche) ? `· niveau ${trame.niveau.affiche}` : '';
  document.getElementById('source').textContent = `· bus ${dimBus} ${niveau}`;

  construireAretes();
}

// Arêtes : toutes les paires (neurone d'entrée consommé → neurone de sortie) dont le poids dépasse
// le seuil. La topologie est DENSE et implicite (§4) : ce sont les poids quantifiés qui décident
// de ce qu'on voit. Les entrées NON neuronales (bornes §5) sont comptées à part, jamais dessinées.
function construireAretes() {
  const paires = [];
  let horsBornes = 0;
  for (const couche of noeuds.couches) {
    const poids = base64EnOctets(couche.poids_i8);
    const entree = Math.max(0, couche.entree | 0);
    const sortie = Math.max(0, couche.sortie | 0);
    // Poids illisible ou échelle non finie = poids ABSENT (même ruling que la tâche 1).
    if (poids.length !== entree * sortie || !Number.isFinite(couche.echelle)) continue;
    for (let o = 0; o < sortie; o++) {
      const base = o * entree;
      const cible = couche._debut + o;
      for (let i = 0; i < entree; i++) {
        // ⚠️ Le seuil est RELATIF au poids le plus fort de la COUCHE (`|i8| / 127`) : `echelle`
        // vaut exactement `max(|w|) / 127` (tâche 1), donc ce rapport EST `|w| / max` — il est
        // comparable d'une couche à l'autre, ce que le curseur 0…1 promet. Comparer des poids
        // ABSOLUS rendrait le curseur inerte : MESURÉ le 10/09/2026 sur la fixture de sonde
        // (poids ~1e-3), le seuil 0,15 ne laissait que 5 arêtes sur 7 152, et 0,60 aucune.
        const valeur = Math.abs((poids[base + i] << 24) >> 24) / 127;
        if (!(valeur >= seuil)) continue;         // `!(…)` : un poids non fini ne passe jamais
        const entreeConsommee = couche._source[i];
        if (entreeConsommee < 0) { horsBornes++; continue; }
        paires.push([noeuds.colonne.debut + entreeConsommee, cible]);
      }
    }
  }
  aretes.paires = paires;
  aretes.horsBornes = horsBornes;
  if (aretes.lignes) { scene.remove(aretes.lignes); aretes.lignes.geometry.dispose(); }
  const sommets = new Float32Array(paires.length * 6);
  aretes.lignes = new THREE.LineSegments(
    new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(sommets, 3)),
    new THREE.LineBasicMaterial({ color: 0x3a5a8a, transparent: true, opacity: 0.35 }));
  scene.add(aretes.lignes);
  rafraichirAretes();
  majPanneau();
}

// ⚠️ Les DEUX extrémités comptent : la source est le neurone du bus qui est RÉELLEMENT consommé
// (sa position est connue, cf. `planDesEntrees`), la cible est le neurone de sortie de la couche.
// Relier un neurone à lui-même produirait des arêtes de longueur nulle — invisibles — tout en
// affichant un compte juste : le seuil semblerait alors ne rien changer.
function rafraichirAretes() {
  if (!aretes.lignes) return;
  const attribut = aretes.lignes.geometry.getAttribute('position');
  const tableau = attribut.array;
  for (let k = 0; k < aretes.paires.length; k++) {
    const a = noeuds.positions[aretes.paires[k][0]];
    const b = noeuds.positions[aretes.paires[k][1]];
    tableau[k * 6 + 0] = a[0]; tableau[k * 6 + 1] = a[1]; tableau[k * 6 + 2] = a[2];
    tableau[k * 6 + 3] = b[0]; tableau[k * 6 + 4] = b[1]; tableau[k * 6 + 5] = b[2];
  }
  attribut.needsUpdate = true;
}

function majPanneau() {
  const colonne = noeuds.colonne ? ` · colonne du bus ${noeuds.colonne.taille}` : '';
  const bornes = aretes.horsBornes ? ` · ${aretes.horsBornes} entrées non neuronales (bornes)` : '';
  const trous = noeuds.sansPositions ? ` · ⚠️ ${noeuds.sansPositions} plaque(s) sans positions` : '';
  document.getElementById('structure').textContent =
    `${noeuds.couches.length} couches · ${noeuds.neurones} neurones${colonne}` +
    ` · ${aretes.paires.length} arêtes ≥ ${seuil.toFixed(2)}${bornes}${trous}`;
}

// --- 5. L'activité : une couleur par neurone, auto-calibrée sur la trame ----------------------
function appliquerActivite(trame) {
  if (!noeuds.maillage || !noeuds.couches.length) return;
  const brutes = (trame && trame.neurones) || {};
  const parCouche = {};
  let maximum = 1e-6;
  for (const couche of noeuds.couches) {
    const valeurs = float16VersFloat32(base64EnOctets(brutes[couche.nom]));
    // ⚠️ Ruling : `null`, champ manquant, ou longueur qui ne correspond pas à la plaque = une
    // activation ABSENTE — neurones GRIS. On ne complète pas les manquants, on ne les invente pas.
    const lisible = valeurs.length === Math.max(0, couche.sortie | 0) ? valeurs : null;
    parCouche[couche.nom] = lisible;
    if (lisible) {
      for (const valeur of lisible) {
        if (Number.isFinite(valeur)) maximum = Math.max(maximum, valeur);
      }
    }
  }
  for (const couche of noeuds.couches) {
    const valeurs = parCouche[couche.nom];
    for (let i = 0; i < Math.max(0, couche.sortie | 0); i++) {
      noeuds.maillage.setColorAt(couche._debut + i,
                                 couleurActivation(valeurs ? valeurs[i] : NaN, maximum));
    }
  }
  noeuds.maillage.instanceColor.needsUpdate = true;
  const s = (trame && trame.scalaires) || {};
  document.getElementById('infos').textContent =
    `jour ${nombre(trame && trame.jour, '—')} · tick ${nombre(trame && trame.tick, '—')}` +
    ` · dopamine ${nombre(s.dopamine, 0).toFixed(3)}` +
    ` · planification ${nombre(s.force_planification, 0).toFixed(2)}` +
    ` · action ${Number.isFinite(s.action) ? s.action : '—'}`;
}

// --- 6. Le flux : un seul canal, trois types d'événements (§4 de la spec) ---------------------
const flux = new EventSource('/flux');
flux.addEventListener('structure', e => construireStructure(JSON.parse(e.data)));
flux.addEventListener('activite', e => appliquerActivite(JSON.parse(e.data)));
flux.addEventListener('evenement', e => {
  const evenement = JSON.parse(e.data);
  document.getElementById('etat').textContent = `⚡ ${evenement.genre} (tick ${evenement.tick})`;
});
flux.onopen = () => { document.getElementById('etat').textContent = 'flux connecté'; };
flux.onerror = () => { document.getElementById('etat').textContent = 'flux interrompu — reconnexion…'; };

// Le seuil : une COMMODITÉ de lecture (§4), jamais une mesure — et l'interface le dit.
const curseur = document.getElementById('seuil');
curseur.addEventListener('input', () => {
  seuil = Number(curseur.value) / 100;
  document.getElementById('valeur-seuil').textContent = seuil.toFixed(2);
  if (noeuds.couches.length) construireAretes();
});

// Les boutons de zoom (demande de l'auteur, 10/09/2026) : le zoom n'existait qu'à la molette,
// donc il était invisible pour qui ne l'essaie pas. Les trois boutons passent par les MÊMES
// fonctions que la molette — `+` rapproche, `−` éloigne, `⟳` recentre.
// Le garde `if (bouton)` : si la page servie est plus ancienne que `app.js` (cache du
// navigateur), l'absence d'un bouton ne doit pas casser l'affichage du cerveau.
for (const [id, action] of [['zoom-plus', () => zoomer(1 / PAS_ZOOM)],
                            ['zoom-moins', () => zoomer(PAS_ZOOM)],
                            ['zoom-recentrer', recentrer]]) {
  const bouton = document.getElementById(id);
  if (bouton) bouton.addEventListener('click', action);
}

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

(function animer() {
  requestAnimationFrame(animer);
  majCamera();
  renderer.render(scene, camera);
})();
