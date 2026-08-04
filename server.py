import http.server
import socketserver
import urllib.request
import urllib.error
import json
import sys
import sqlite3

PORT = 8765
DB_FILE = 'procurement_radar.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS news (
        titre TEXT PRIMARY KEY,
        date TEXT,
        type TEXT,
        resume TEXT,
        source TEXT,
        panel_link TEXT,
        isLive INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        famille TEXT,
        niveau TEXT,
        icon TEXT,
        titre TEXT,
        date TEXT,
        resume TEXT,
        risques TEXT,
        actions TEXT,
        fournisseurs_touches TEXT,
        isLive INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS aos (
        titre TEXT PRIMARY KEY,
        mo TEXT,
        secteur TEXT,
        region TEXT,
        pub TEXT,
        limite TEXT,
        montant TEXT,
        statut TEXT,
        isLive INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS veille (
        id INTEGER PRIMARY KEY,
        nom TEXT,
        type TEXT,
        cat TEXT,
        dirigeant TEXT,
        signal TEXT,
        action TEXT,
        solution TEXT,
        date TEXT,
        source TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ma (
        id INTEGER PRIMARY KEY,
        type TEXT,
        impact TEXT,
        secteur TEXT,
        date TEXT,
        acteurs TEXT,
        detail TEXT,
        montant TEXT,
        source TEXT,
        panel_impact TEXT
    )''')
    conn.commit()
    conn.close()
    print("[Database] SQLite initialized successfully.", flush=True)

def load_all_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # News
    c.execute("SELECT titre, date, type, resume, source, panel_link, isLive FROM news")
    news_rows = c.fetchall()
    news = []
    for r in news_rows:
        news.append({
            "titre": r[0],
            "date": r[1],
            "type": r[2],
            "resume": r[3],
            "source": r[4],
            "panel_link": r[5],
            "isLive": bool(r[6])
        })
        
    # Tenders (AOs)
    c.execute("SELECT titre, mo, secteur, region, pub, limite, montant, statut, isLive FROM aos")
    aos_rows = c.fetchall()
    aos = []
    for r in aos_rows:
        aos.append({
            "titre": r[0],
            "mo": r[1],
            "secteur": r[2],
            "region": r[3],
            "pub": r[4],
            "limite": r[5],
            "montant": r[6],
            "statut": r[7],
            "isLive": bool(r[8])
        })
        
    # Alerts
    c.execute("SELECT id, famille, niveau, icon, titre, date, resume, risques, actions, fournisseurs_touches, isLive FROM alerts")
    alerts_rows = c.fetchall()
    alerts = []
    for r in alerts_rows:
        try:
            risques = json.loads(r[7])
        except Exception:
            risques = []
        try:
            actions = json.loads(r[8])
        except Exception:
            actions = []
        try:
            fournisseurs_touches = json.loads(r[9])
        except Exception:
            fournisseurs_touches = []
            
        alerts.append({
            "id": r[0],
            "famille": r[1],
            "niveau": r[2],
            "icon": r[3],
            "titre": r[4],
            "date": r[5],
            "resume": r[6],
            "risques": risques,
            "actions": actions,
            "fournisseurs_touches": fournisseurs_touches,
            "isLive": bool(r[10])
        })
        
    # Veille
    c.execute("SELECT id, nom, type, cat, dirigeant, signal, action, solution, date, source FROM veille")
    veille_rows = c.fetchall()
    veille = []
    for r in veille_rows:
        veille.append({
            "id": r[0],
            "nom": r[1],
            "type": r[2],
            "cat": r[3],
            "dirigeant": r[4],
            "signal": r[5],
            "action": r[6],
            "solution": r[7],
            "date": r[8],
            "source": r[9]
        })
        
    # M&A
    c.execute("SELECT id, type, impact, secteur, date, acteurs, detail, montant, source, panel_impact FROM ma")
    ma_rows = c.fetchall()
    ma = []
    for r in ma_rows:
        try:
            acteurs = json.loads(r[5])
        except Exception:
            acteurs = [r[5]] if r[5] else []
        ma.append({
            "id": r[0],
            "type": r[1],
            "impact": r[2],
            "secteur": r[3],
            "date": r[4],
            "acteurs": acteurs,
            "detail": r[6],
            "montant": r[7],
            "source": r[8],
            "panel_impact": r[9]
        })
        
    conn.close()
    return {
        "news": news,
        "aos": aos,
        "alerts": alerts,
        "veille": veille,
        "ma": ma
    }

def save_all_data(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if "news" in data:
        c.execute("DELETE FROM news")
        for item in data["news"]:
            c.execute("INSERT OR REPLACE INTO news (titre, date, type, resume, source, panel_link, isLive) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (item.get("titre"), item.get("date"), item.get("type"), item.get("resume"), item.get("source"), item.get("panel_link"), 1 if item.get("isLive") else 0))
                      
    if "aos" in data:
        c.execute("DELETE FROM aos")
        for item in data["aos"]:
            c.execute("INSERT OR REPLACE INTO aos (titre, mo, secteur, region, pub, limite, montant, statut, isLive) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (item.get("titre"), item.get("mo"), item.get("secteur"), item.get("region"), item.get("pub"), item.get("limite"), item.get("montant"), item.get("statut"), 1 if item.get("isLive") else 0))
                      
    if "alerts" in data:
        c.execute("DELETE FROM alerts")
        for item in data["alerts"]:
            risques = json.dumps(item.get("risques", []))
            actions = json.dumps(item.get("actions", []))
            fournisseurs_touches = json.dumps(item.get("fournisseurs_touches", []))
            c.execute("INSERT OR REPLACE INTO alerts (id, famille, niveau, icon, titre, date, resume, risques, actions, fournisseurs_touches, isLive) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (item.get("id"), item.get("famille"), item.get("niveau"), item.get("icon"), item.get("titre"), item.get("date"), item.get("resume"), risques, actions, fournisseurs_touches, 1 if item.get("isLive") else 0))
                      
    if "veille" in data:
        c.execute("DELETE FROM veille")
        for item in data["veille"]:
            c.execute("INSERT OR REPLACE INTO veille (id, nom, type, cat, dirigeant, signal, action, solution, date, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (item.get("id"), item.get("nom"), item.get("type"), item.get("cat"), item.get("dirigeant"), item.get("signal"), item.get("action"), item.get("solution"), item.get("date"), item.get("source")))
                      
    if "ma" in data:
        c.execute("DELETE FROM ma")
        for item in data["ma"]:
            acteurs = json.dumps(item.get("acteurs", []))
            c.execute("INSERT OR REPLACE INTO ma (id, type, impact, secteur, date, acteurs, detail, montant, source, panel_impact) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (item.get("id"), item.get("type"), item.get("impact"), item.get("secteur"), item.get("date"), acteurs, item.get("detail"), item.get("montant"), item.get("source"), item.get("panel_impact")))
                      
    conn.commit()
    conn.close()
    print("[Database] Saved all data successfully.", flush=True)

def search_ddg(query):
    import urllib.request
    import urllib.parse
    from bs4 import BeautifulSoup
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = 'https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': query})
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            charset = response.info().get_content_charset() or 'utf-8'
            html = response.read().decode(charset, errors='replace')
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            for elem in soup.select('.result__snippet'):
                results.append(elem.get_text().strip())
            return results[:8]
    except Exception as e:
        print(f"[Search] Error querying DDG: {e}", flush=True)
        return []

def get_search_query(user_prompt):
    user_prompt_lower = user_prompt.lower()
    if "actualites recentes" in user_prompt_lower:
        return "actualités entreprises Maroc"
    elif "alertes marche" in user_prompt_lower:
        return "marchés publics Maroc actualité achats"
    elif "brent" in user_prompt_lower and "bdi" in user_prompt_lower:
        return "brent crude oil price baltic dry index crb index today"
    
    cleaned = user_prompt
    for stop_word in ["important :", "json :", "donne en json", "ne renvoie pas", "classe tabler"]:
        if stop_word in cleaned.lower():
            idx = cleaned.lower().find(stop_word)
            cleaned = cleaned[:idx]
            
    query = cleaned.strip().replace("\n", " ")
    if len(query) > 100:
        query = query[:100]
    return query

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            try:
                data = load_all_data()
                res_bytes = json.dumps(data).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(res_bytes)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(res_bytes)
            except Exception as e:
                print(f"[Server] Error getting DB data: {e}", flush=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        print(f"[Proxy] POST request received for path: {self.path}", flush=True)
        if self.path == '/api/claude':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Extract headers from incoming request
            api_key = self.headers.get('x-api-key', '')
            version = self.headers.get('anthropic-version', '2023-06-01')
            beta = self.headers.get('anthropic-beta', '')
            
            print(f"[Proxy] API Key starts with: {api_key[:12]}...", flush=True)
            print(f"[Proxy] Version: {version}, Beta: {beta}", flush=True)
            
            # Prepare request to Anthropic
            url = 'https://api.anthropic.com/v1/messages'
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_key,
                'Anthropic-Version': version,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProcurementRadarProxy/1.0'
            }
            if beta:
                headers['Anthropic-Beta'] = beta
                
            print(f"[Proxy] Forwarding request to Anthropic: {url}", flush=True)
            req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
            
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = response.read()
                    print(f"[Proxy] Success from Anthropic: {response.status}", flush=True)
                    try:
                        import os
                        scratch_dir = r"C:\Users\HP\.gemini\antigravity-ide\brain\38867b0c-f11e-4fd8-b06c-df341db01dbf\scratch"
                        os.makedirs(scratch_dir, exist_ok=True)
                        with open(os.path.join(scratch_dir, "last_req_resp.json"), "wb") as f:
                            f.write(b"REQUEST:\n")
                            f.write(post_data)
                            f.write(b"\n\nRESPONSE:\n")
                            f.write(res_data)
                    except Exception as ex:
                        print(f"[Proxy] Error saving debug file: {ex}", flush=True)
                    self.send_response(response.status)
                    
                    # Forward key headers (including content-length!)
                    for header, val in response.getheaders():
                        if header.lower() in ['content-type', 'content-length', 'anthropic-version']:
                            self.send_header(header, val)
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self.wfile.write(res_data)
            except urllib.error.HTTPError as e:
                res_data = e.read()
                print(f"[Proxy] HTTPError from Anthropic: {e.code} - {e.reason}", flush=True)
                try:
                    err_msg = res_data.decode('utf-8', errors='replace')
                    print(f"[Proxy] Error message from Anthropic: {err_msg}", flush=True)
                except Exception as ex:
                    pass
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(res_data)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(res_data)
            except Exception as e:
                print(f"[Proxy] General Exception: {str(e)}", flush=True)
                err_data = json.dumps({'error': {'message': str(e)}}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_data)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(err_data)
        elif self.path == '/api/save_data':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                save_all_data(data)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"[Server] Error saving data: {e}", flush=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        elif self.path == '/api/gemini':
            # Extract Gemini Key from header
            gemini_key = self.headers.get('X-Gemini-Key')
            if not gemini_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing X-Gemini-Key header"}).encode('utf-8'))
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Forward to Gemini API
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}'
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"[Proxy] Forwarding request to Gemini: {url}", flush=True)
            req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
            
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = response.read()
                    print(f"[Proxy] Success from Gemini: {response.status}", flush=True)
                    self.send_response(response.status)
                    for header, val in response.getheaders():
                        if header.lower() in ['content-type', 'content-length']:
                            self.send_header(header, val)
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self.wfile.write(res_data)
            except urllib.error.HTTPError as e:
                err_content = e.read()
                print(f"[Proxy] HTTP Error from Gemini: {e.code} - {err_content.decode('utf-8', errors='replace')}", flush=True)
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_content)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(err_content)
            except Exception as e:
                print(f"[Proxy] General Exception forwarding to Gemini: {e}", flush=True)
                err_msg = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_msg)))
                self.end_headers()
                self.wfile.write(err_msg)
        elif self.path == '/api/mistral':
            # Extract Mistral Key from header
            mistral_key = self.headers.get('X-Mistral-Key')
            if not mistral_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing X-Mistral-Key header"}).encode('utf-8'))
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                if payload.get('web_search'):
                    messages = payload.get('messages', [])
                    user_msg_idx = -1
                    for idx in range(len(messages) - 1, -1, -1):
                        if messages[idx].get('role') == 'user':
                            user_msg_idx = idx
                            break
                    if user_msg_idx != -1:
                        user_prompt = messages[user_msg_idx].get('content', '')
                        search_query = get_search_query(user_prompt)
                        print(f"[Proxy] Web search enabled for Mistral. Querying DDG: {search_query}", flush=True)
                        snippets = search_ddg(search_query)
                        if snippets:
                            search_context = "\n".join([f"- {s}" for s in snippets])
                            import datetime
                            today_str = datetime.date.today().strftime("%Y-%m-%d")
                            enrichment = f"\n\n[CONTEXTE DE RECHERCHE WEB RÉEL ET VÉRIFIÉ (Aujourd'hui: {today_str})]:\n{search_context}\n\nUtilise UNIQUEMENT les faits réels ci-dessus. Si l'information demandée n'y figure pas ou si les résultats sont vides, retourne une liste vide JSON selon le format demandé sans rien inventer."
                            messages[user_msg_idx]['content'] = user_prompt + enrichment
                
                # Remove custom search key before forwarding
                payload.pop('web_search', None)
                post_data = json.dumps(payload).encode('utf-8')
            except Exception as e:
                print(f"[Proxy] Error processing web search for Mistral: {e}", flush=True)
            
            # Forward to Mistral API
            url = 'https://api.mistral.ai/v1/chat/completions'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mistral_key}'
            }
            
            print(f"[Proxy] Forwarding request to Mistral: {url}", flush=True)
            req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
            
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = response.read()
                    print(f"[Proxy] Success from Mistral: {response.status}", flush=True)
                    self.send_response(response.status)
                    for header, val in response.getheaders():
                        if header.lower() in ['content-type', 'content-length']:
                            self.send_header(header, val)
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self.wfile.write(res_data)
            except urllib.error.HTTPError as e:
                err_content = e.read()
                print(f"[Proxy] HTTP Error from Mistral: {e.code} - {err_content.decode('utf-8', errors='replace')}", flush=True)
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_content)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(err_content)
            except Exception as e:
                print(f"[Proxy] General Exception forwarding to Mistral: {e}", flush=True)
                err_msg = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_msg)))
                self.end_headers()
                self.wfile.write(err_msg)
        else:
            print(f"[Proxy] Path not matched: {self.path}. Returning 404.", flush=True)
            self.send_response(404)
            self.end_headers()

Handler = ProxyHTTPRequestHandler

# Enable reuse address to avoid 'Address already in use' errors
socketserver.TCPServer.allow_reuse_address = True

if __name__ == '__main__':
    init_db()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Procurement Radar running on http://localhost:{PORT}", flush=True)
        print("AI Proxy active on http://localhost:8765/api/claude", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...", flush=True)
            sys.exit(0)
