import pygame, random

pygame.init()
pygame.font.init()

W, H, T = 400, 400, 100  # Larghezza, Altezza, Dimensione Tile (40px)
schermo = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
font = pygame.font.SysFont("courier", 20, bold=True)

# LA MACCHINA A STATI
stato = "MAPPA" # Può essere: "MAPPA", "BATTAGLIA", "MORTO"

# Variabili Mappa
px, py  = W // 2, H // 2

# Statistiche RPG
hp_max = 50
hp = hp_max
nemico_hp_max = 30
nemico_hp = nemico_hp_max

# Interfaccia Battaglia
menu = ["ATTACCA", "FUGGI"]
sel = 0 # Indice del menu
msg = ""

# --- NUOVO CODICE SPRITE ---
# Carica l'immagine e mantieni la trasparenza
sprite_gatto = pygame.image.load("gatto.png").convert_alpha()

# Scala il gatto per farlo entrare nella casella della mappa (40x40 pixel)
gatto_mappa = pygame.transform.scale(sprite_gatto, (T, T))

# Scala un gatto più grande per la schermata di battaglia (100x100 pixel)
gatto_battaglia = pygame.transform.scale(sprite_gatto, (100, 100))
# ---------------------------
while True:
    clock.tick(15) # Framerate volutamente basso per simulare i vecchi GameBoy

    for e in pygame.event.get():
        if e.type == pygame.QUIT: exit()
        
        if e.type == pygame.KEYDOWN:
            # --- LOGICA STATO: ESPLORAZIONE ---
            if stato == "MAPPA":
                old_px, old_py = px, py
                if e.key == pygame.K_LEFT:  px -=T
                if e.key == pygame.K_RIGHT: px += T
                if e.key == pygame.K_UP: py -= T
                if e.key == pygame.K_DOWN: py += T
                
                # Blocca sui bordi dello schermo
                px = max(0, min(W - T, px))
                py = max(0, min(H - T, py))
                
                # Roll per Incontro Casuale (solo se hai effettivamente fatto un passo)
                if (px != old_px or py != old_py) and random.random() < 0.15:
                    stato = "BATTAGLIA"
                    nemico_hp = nemico_hp_max # Spawna un nemico nuovo
                    msg = "UN NEMICO SELVATICO!"
                    sel = 0

            # --- LOGICA STATO: COMBATTIMENTO ---
            elif stato == "BATTAGLIA":
                if e.key == pygame.K_UP: sel = max(0, sel - 1)
                if e.key == pygame.K_DOWN: sel = min(1, sel + 1)
                
                if e.key == pygame.K_RETURN or e.key == pygame.K_SPACE:
                    if menu[sel] == "FUGGI":
                        stato = "MAPPA"
                    
                    elif menu[sel] == "ATTACCA":
                        # Turno del Giocatore
                        danno = random.randint(10, 20)
                        nemico_hp -= danno
                        msg = f"HAI FATTO {danno} DANNI!"
                        
                        if nemico_hp <= 0:
                            msg = "NEMICO SCONFITTO!"
                            stato = "MAPPA" # Vittoria: torna alla mappa
                        else:
                            # Contropiede del Nemico
                            danno_n = random.randint(5, 15)
                            hp -= danno_n
                            if hp <= 0:
                                stato = "MORTO"

            # --- LOGICA STATO: GAME OVER ---
            elif stato == "MORTO":
                if e.key == pygame.K_r:
                    hp = hp_max
                    px, py = W // 2, H // 2
                    stato = "MAPPA"

    # ==========================
    # ENGINE GRAFICO (RENDERING)
    # ==========================
    
    if stato == "MAPPA":
        schermo.fill((34, 139, 34)) # Sfondo verde (Erba alta)
        #pygame.draw.rect(schermo, (0, 100, 255), (px, py, T, T)) # Giocatore
        schermo.blit(gatto_mappa, (px, py))
        
    elif stato == "BATTAGLIA":
        schermo.fill((0, 0, 0)) # Sfondo nero
        
        # Sprite placeholder
        pygame.draw.rect(schermo, (255, 0, 0), (250, 50, 100, 100)) # Nemico (Rosso in alto a dx)
        schermo.blit(gatto_battaglia, (50, 180))        
        # Barra HUD in basso
        pygame.draw.rect(schermo, (200, 200, 200), (0, 300, W, 100))
        pygame.draw.rect(schermo, (0, 0, 0), (5, 305, W-10, 90), 2) # Bordo HUD
        
        # Statistiche in alto
        schermo.blit(font.render(f"TU: {hp}/{hp_max} HP", True, (255, 255, 255)), (10, 10))
        schermo.blit(font.render(f"NEMICO: {nemico_hp} HP", True, (255, 0, 0)), (250, 10))
        
        # Testo descrittivo
        schermo.blit(font.render(msg, True, (0, 0, 0)), (20, 320))
        
        # Cursore Menu (Destra HUD)
        for i, opt in enumerate(menu):
            colore_testo = (255, 0, 0) if i == sel else (0, 0, 0)
            schermo.blit(font.render(opt, True, colore_testo), (280, 320 + i * 30))

    elif stato == "MORTO":
        schermo.fill((0, 0, 0))
        txt = font.render("SEI SVENUTO. PREMI R", True, (255, 0, 0))
        schermo.blit(txt, (W//2 - txt.get_width()//2, H//2))

    pygame.display.flip()