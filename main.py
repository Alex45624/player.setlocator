import os
import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog


# ============================================================
# PLAYER.SET.LOCATOR
# V4.5
# ============================================================

APP_NAME = "PLAYER.SET.LOCATOR"
VERSION = "4.5"

# ============================================================
# PALETA
# SOMENTE PRETO / VERMELHO / VERMELHO ESCURO
# ============================================================

BLACK = "#050505"
BLACK_2 = "#080808"
BLACK_3 = "#0C0C0C"

RED_DARK = "#25080C"
RED_DARK_2 = "#351016"
RED = "#A81220"
RED_BRIGHT = "#C81728"
RED_SOFT = "#7F0E19"

WHITE = "#F0F0F0"
GRAY = "#A0A0A0"
GRAY_DARK = "#686868"

BORDER = "#241014"
BORDER_RED = "#4A1018"


# ============================================================
# OTIMIZAÇÃO
# ============================================================

MAX_CONTENT_SIZE = 10 * 1024 * 1024
READ_BLOCK = 128 * 1024

MAX_VISIBLE_RESULTS = 600

# Atualização visual em lotes.
QUEUE_INTERVAL = 120
STATS_INTERVAL = 250

# Extensões onde a busca de conteúdo faz sentido.
TEXT_EXTENSIONS = {
    ".txt",
    ".log",
    ".ini",
    ".cfg",
    ".conf",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".html",
    ".htm",
    ".css",
    ".md",
    ".bat",
    ".cmd",
    ".ps1",
    ".sql",
    ".toml",
    ".properties",
    ".csv",
    ".tsv",
}


# ============================================================
# JANELA
# ============================================================

root = tk.Tk()

root.title(f"{APP_NAME}  |  {VERSION}")

# Janela normal, não fullscreen.
root.geometry("1180x760")
root.minsize(1000, 680)

root.configure(bg=BLACK)


# ============================================================
# ESTADO
# ============================================================

terms_accepted = False

searching = False
stop_requested = False

stop_event = threading.Event()

result_queue = queue.Queue()

results = []
result_keys = set()

session_history = []

selected_folder = None

search_started = 0.0

files_scanned = 0
matches_found = 0
errors_count = 0

current_page = "search"

ui_update_running = False
search_finished_handled = False

progress_offset = 0


# ============================================================
# REFERÊNCIAS DE INTERFACE
# ============================================================

search_page = None
files_page = None
settings_page = None
about_page = None

search_entry = None
mode_var = None
content_var = None

folder_label = None

results_container = None
results_canvas = None

result_count_label = None

files_stat_label = None
speed_stat_label = None
time_stat_label = None
errors_stat_label = None

progress_canvas = None
progress_text = None

status_text = None

start_button = None
stop_button = None

history_container = None

nav_search = None
nav_files = None
nav_settings = None
nav_about = None


# ============================================================
# FUNÇÕES BÁSICAS
# ============================================================

def clear_root():
    for child in root.winfo_children():
        child.destroy()


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def format_number(value):
    return f"{safe_int(value):,}".replace(",", ".")


def format_time(seconds):
    seconds = max(0, int(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def set_status(text):
    if status_text is not None:
        status_text.configure(text=text)


# ============================================================
# BOTÕES
# ============================================================

def configure_button(button, primary=False):

    if primary:

        button.configure(
            bg=RED,
            fg=WHITE,
            activebackground=RED_BRIGHT,
            activeforeground=WHITE,
            disabledforeground=GRAY_DARK,
            relief="flat",
            bd=0,
            cursor="hand2"
        )

    else:

        button.configure(
            bg=BLACK_3,
            fg=WHITE,
            activebackground=RED_DARK,
            activeforeground=WHITE,
            disabledforeground=GRAY_DARK,
            relief="flat",
            bd=1,
            highlightthickness=0,
            cursor="hand2"
        )


# ============================================================
# DIALOG PERSONALIZADO
# ============================================================

def show_dialog(
    title,
    message,
    kind="info",
    buttons=None
):
    """
    Dialog próprio do programa.
    Evita os messagebox brancos padrão do Windows.
    """

    if buttons is None:
        buttons = [("OK", True)]

    dialog = tk.Toplevel(root)

    dialog.title(APP_NAME)
    dialog.geometry("520x280")
    dialog.minsize(450, 240)

    dialog.configure(bg=BLACK)

    dialog.transient(root)
    dialog.grab_set()

    result = {"value": False}

    # Cabeçalho
    header = tk.Frame(
        dialog,
        bg=BLACK
    )

    header.pack(
        fill="x",
        padx=25,
        pady=(22, 10)
    )

    line = tk.Frame(
        header,
        bg=RED,
        width=4,
        height=38
    )

    line.pack(
        side="left",
        fill="y"
    )

    title_frame = tk.Frame(
        header,
        bg=BLACK
    )

    title_frame.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(12, 0)
    )

    tk.Label(
        title_frame,
        text=title.upper(),
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 12, "bold")
    ).pack(
        anchor="w"
    )

    if kind == "warning":
        subtitle = "ATENÇÃO"
    elif kind == "error":
        subtitle = "ERRO"
    else:
        subtitle = "PLAYER.SET.LOCATOR"

    tk.Label(
        title_frame,
        text=subtitle,
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 8, "bold")
    ).pack(
        anchor="w",
        pady=(2, 0)
    )

    # Mensagem
    message_frame = tk.Frame(
        dialog,
        bg=BLACK_2
    )

    message_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=5
    )

    tk.Label(
        message_frame,
        text=message,
        bg=BLACK_2,
        fg=GRAY,
        justify="left",
        anchor="nw",
        wraplength=440,
        font=("Segoe UI", 10)
    ).pack(
        fill="both",
        expand=True,
        padx=18,
        pady=15
    )

    # Botões
    button_bar = tk.Frame(
        dialog,
        bg=BLACK
    )

    button_bar.pack(
        fill="x",
        padx=25,
        pady=(8, 20)
    )

    def close(value):
        result["value"] = value
        dialog.destroy()

    for text, value in reversed(buttons):

        button = tk.Button(
            button_bar,
            text=text,
            command=lambda v=value: close(v),
            font=("Segoe UI", 9, "bold"),
            padx=20,
            pady=8
        )

        configure_button(
            button,
            primary=(text.upper() in ("OK", "CONTINUAR", "CONCORDO", "SIM"))
        )

        button.pack(
            side="right",
            padx=(7, 0)
        )

    dialog.protocol(
        "WM_DELETE_WINDOW",
        lambda: close(False)
    )

    root.wait_window(dialog)

    return result["value"]


# ============================================================
# TERMOS
# ============================================================

def show_terms_screen():

    global terms_accepted

    terms_accepted = False

    clear_root()

    root.title(
        f"{APP_NAME}  |  TERMOS DE USO"
    )

    root.geometry("1050x720")
    root.minsize(900, 650)

    outer = tk.Frame(
        root,
        bg=BLACK
    )

    outer.pack(
        fill="both",
        expand=True
    )

    # --------------------------------------------------------
    # TOPO
    # --------------------------------------------------------

    top = tk.Frame(
        outer,
        bg=BLACK
    )

    top.pack(
        fill="x",
        padx=55,
        pady=(40, 15)
    )

    tk.Label(
        top,
        text=APP_NAME,
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 13, "bold")
    ).pack(
        anchor="w"
    )

    tk.Label(
        top,
        text="TERMOS DE USO",
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 28, "bold")
    ).pack(
        anchor="w",
        pady=(4, 0)
    )

    tk.Label(
        top,
        text="Leia as condições antes de entrar no programa.",
        bg=BLACK,
        fg=GRAY,
        font=("Segoe UI", 10)
    ).pack(
        anchor="w",
        pady=(5, 0)
    )

    # --------------------------------------------------------
    # PAINEL
    # --------------------------------------------------------

    panel = tk.Frame(
        outer,
        bg=BLACK_2,
        highlightbackground=BORDER_RED,
        highlightthickness=1
    )

    panel.pack(
        fill="both",
        expand=True,
        padx=55,
        pady=(5, 15)
    )

    # Barra superior vermelha
    tk.Frame(
        panel,
        bg=RED,
        height=3
    ).pack(
        fill="x"
    )

    text_area = tk.Frame(
        panel,
        bg=BLACK_2
    )

    text_area.pack(
        fill="both",
        expand=True,
        padx=28,
        pady=25
    )

    terms_text = tk.Text(
        text_area,
        bg=BLACK_2,
        fg="#D0D0D0",
        insertbackground=RED_BRIGHT,
        selectbackground=RED_DARK_2,
        selectforeground=WHITE,
        relief="flat",
        bd=0,
        wrap="word",
        font=("Segoe UI", 10),
        padx=5,
        pady=5
    )

    terms_text.pack(
        side="left",
        fill="both",
        expand=True
    )

    scroll = tk.Scrollbar(
        text_area,
        command=terms_text.yview,
        bg=BLACK_3,
        troughcolor=BLACK,
        activebackground=RED,
        relief="flat"
    )

    scroll.pack(
        side="right",
        fill="y"
    )

    terms_text.configure(
        yscrollcommand=scroll.set
    )

    terms = """
PLAYER.SET.LOCATOR

TERMOS DE USO


01  FINALIDADE

O PLAYER.SET.LOCATOR é uma ferramenta local para localização e
pesquisa de arquivos.

A ferramenta permite pesquisar arquivos pelo nome e, quando
habilitado, procurar termos dentro de determinados arquivos
de texto.


02  USO AUTORIZADO

Utilize o programa somente em computadores, pastas e arquivos
aos quais você tenha autorização para acessar.

O programa não deve ser utilizado para contornar permissões,
ocultar atividades ou acessar dados de terceiros sem autorização.


03  PESQUISA

A pesquisa por nome pode verificar arquivos independentemente
da extensão.

A pesquisa por conteúdo é limitada a formatos de texto
compatíveis e possui limites para evitar consumo excessivo
de recursos.


04  COMPUTADOR INTEIRO

A opção "Computador inteiro" pode verificar os discos
disponíveis no sistema.

Essa operação pode utilizar armazenamento, processador e
tempo de execução consideráveis.


05  PARAR

A pesquisa pode ser interrompida pelo botão PARAR.

A interrupção pode levar alguns instantes caso o programa
esteja concluindo uma operação de leitura naquele momento.


06  VISUALIZADOR

O visualizador é somente leitura.

Arquivos maiores que 10 MB não são carregados.

O PLAYER.SET.LOCATOR não executa os arquivos encontrados.


07  SESSÃO

O histórico apresentado dentro da página ARQUIVOS corresponde
à sessão atual do programa.


08  RESPONSABILIDADE

O usuário é responsável pelo uso adequado da ferramenta e por
respeitar as permissões existentes no computador utilizado.


Ao clicar em CONCORDO, você confirma que leu e compreendeu
estes termos e deseja continuar para o programa.
"""

    terms_text.insert(
        "1.0",
        terms
    )

    terms_text.configure(
        state="disabled"
    )

    # --------------------------------------------------------
    # BOTÕES
    # --------------------------------------------------------

    buttons = tk.Frame(
        outer,
        bg=BLACK,
        height=65
    )

    buttons.pack(
        fill="x",
        padx=55,
        pady=(0, 28)
    )

    buttons.pack_propagate(False)

    def refuse():
        root.destroy()

    def accept():

        global terms_accepted

        terms_accepted = True

        build_application()

    refuse_button = tk.Button(
        buttons,
        text="NÃO CONCORDO",
        command=refuse,
        font=("Segoe UI", 9, "bold"),
        padx=24,
        pady=10
    )

    configure_button(
        refuse_button,
        primary=False
    )

    refuse_button.pack(
        side="left"
    )

    accept_button = tk.Button(
        buttons,
        text="CONCORDO",
        command=accept,
        font=("Segoe UI", 9, "bold"),
        padx=30,
        pady=10
    )

    configure_button(
        accept_button,
        primary=True
    )

    accept_button.pack(
        side="right"
    )

    root.protocol(
        "WM_DELETE_WINDOW",
        refuse
    )


# ============================================================
# DISCOS
# ============================================================

def get_windows_drives():

    drives = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":

        drive = f"{letter}:\\"

        try:

            if os.path.exists(drive):
                drives.append(drive)

        except OSError:
            pass

    return drives


# ============================================================
# CONTEÚDO
# ============================================================

def file_contains_term(path, wanted):

    try:

        size = path.stat().st_size

        if size > MAX_CONTENT_SIZE:
            return False

        wanted_text = wanted.casefold()

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            while True:

                if stop_event.is_set():
                    return False

                chunk = file.read(READ_BLOCK)

                if not chunk:
                    break

                if wanted_text in chunk.casefold():
                    return True

    except (
        PermissionError,
        OSError,
        UnicodeError,
        ValueError
    ):
        return False

    return False


# ============================================================
# SCANNER ITERATIVO
# ============================================================

def scan_root(
    root_path,
    term,
    search_content
):

    global files_scanned
    global matches_found
    global errors_count

    stack = [root_path]

    term_folded = term.casefold()

    while stack:

        if stop_event.is_set():
            return

        current = stack.pop()

        try:

            with os.scandir(current) as entries:

                for entry in entries:

                    if stop_event.is_set():
                        return

                    try:

                        # Evita links simbólicos.
                        if entry.is_symlink():
                            continue

                        if entry.is_dir(
                            follow_symlinks=False
                        ):

                            stack.append(
                                entry.path
                            )

                            continue

                        if not entry.is_file(
                            follow_symlinks=False
                        ):
                            continue

                        files_scanned += 1

                        filename = entry.name

                        # ------------------------------------------------
                        # BUSCA PELO NOME
                        # ------------------------------------------------

                        if term_folded in filename.casefold():

                            result_queue.put(
                                Path(entry.path)
                            )

                            matches_found += 1

                            continue

                        # ------------------------------------------------
                        # BUSCA PELO CONTEÚDO
                        # ------------------------------------------------

                        if not search_content:
                            continue

                        extension = (
                            Path(filename)
                            .suffix
                            .lower()
                        )

                        if extension not in TEXT_EXTENSIONS:
                            continue

                        path = Path(entry.path)

                        if file_contains_term(
                            path,
                            term
                        ):

                            result_queue.put(path)

                            matches_found += 1

                    except (
                        PermissionError,
                        OSError,
                        ValueError
                    ):

                        errors_count += 1

        except (
            PermissionError,
            OSError,
            ValueError
        ):

            errors_count += 1


# ============================================================
# WORKER
# ============================================================

def search_worker(
    term,
    mode,
    folder,
    search_content
):

    global searching
    global search_finished_handled

    try:

        if mode == "folder":

            if folder:

                scan_root(
                    str(folder),
                    term,
                    search_content
                )

        elif mode == "computer":

            drives = get_windows_drives()

            for drive in drives:

                if stop_event.is_set():
                    break

                scan_root(
                    drive,
                    term,
                    search_content
                )

    finally:

        searching = False


# ============================================================
# RESULTADOS
# ============================================================

def create_result_card(path):

    if results_container is None:
        return

    card = tk.Frame(
        results_container,
        bg=BLACK_2,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    card.pack(
        fill="x",
        padx=8,
        pady=4
    )

    # Barra vermelha lateral
    tk.Frame(
        card,
        bg=RED_DARK_2,
        width=3
    ).pack(
        side="left",
        fill="y"
    )

    information = tk.Frame(
        card,
        bg=BLACK_2
    )

    information.pack(
        side="left",
        fill="both",
        expand=True,
        padx=15,
        pady=11
    )

    tk.Label(
        information,
        text=path.name,
        bg=BLACK_2,
        fg=WHITE,
        anchor="w",
        font=("Segoe UI", 10, "bold")
    ).pack(
        fill="x"
    )

    tk.Label(
        information,
        text=str(path.parent),
        bg=BLACK_2,
        fg=GRAY_DARK,
        anchor="w",
        font=("Segoe UI", 8)
    ).pack(
        fill="x",
        pady=(3, 0)
    )

    open_button = tk.Button(
        card,
        text="VISUALIZAR",
        command=lambda p=path: view_file(p),
        font=("Segoe UI", 8, "bold"),
        padx=13,
        pady=7
    )

    configure_button(
        open_button
    )

    open_button.pack(
        side="right",
        padx=15
    )


def drain_result_queue():

    global ui_update_running

    if results_container is None:
        return

    processed = 0

    while processed < 80:

        try:
            path = result_queue.get_nowait()

        except queue.Empty:
            break

        key = str(path).casefold()

        if key in result_keys:
            continue

        result_keys.add(key)
        results.append(path)

        if len(results) <= MAX_VISIBLE_RESULTS:
            create_result_card(path)

        processed += 1

    update_search_header()

    if searching:
        root.after(
            QUEUE_INTERVAL,
            drain_result_queue
        )

    else:

        # Ainda pode haver resultados esperando na fila.
        if not result_queue.empty():

            root.after(
                30,
                drain_result_queue
            )

        else:

            finish_search()


# ============================================================
# ATUALIZAÇÃO DO CABEÇALHO
# ============================================================

def update_search_header():

    if result_count_label is not None:

        result_count_label.configure(
            text=(
                f"{format_number(matches_found)} "
                f"RESULTADOS"
            )
        )


# ============================================================
# ESTATÍSTICAS
# ============================================================

def update_statistics():

    if not searching:
        return

    elapsed = time.time() - search_started

    if elapsed <= 0:
        elapsed = 0.001

    speed = files_scanned / elapsed

    if files_stat_label is not None:

        files_stat_label.configure(
            text=(
                "ARQUIVOS\n"
                + format_number(files_scanned)
            )
        )

    if speed_stat_label is not None:

        speed_stat_label.configure(
            text=(
                "VELOCIDADE\n"
                + format_number(int(speed))
                + " /s"
            )
        )

    if time_stat_label is not None:

        time_stat_label.configure(
            text=(
                "TEMPO\n"
                + format_time(elapsed)
            )
        )

    if errors_stat_label is not None:

        errors_stat_label.configure(
            text=(
                "ERROS\n"
                + format_number(errors_count)
            )
        )

    root.after(
        STATS_INTERVAL,
        update_statistics
    )


# ============================================================
# PROGRESSO VISUAL
# ============================================================

def animate_progress():

    global progress_offset

    if progress_canvas is None:
        return

    if not searching:
        return

    progress_offset += 8

    width = progress_canvas.winfo_width()

    if width <= 0:
        width = 400

    progress_canvas.delete("progress")

    segment = 180

    start = progress_offset % (width + segment) - segment
    end = start + segment

    progress_canvas.create_rectangle(
        start,
        0,
        end,
        4,
        fill=RED,
        outline="",
        tags="progress"
    )

    root.after(
        40,
        animate_progress
    )


# ============================================================
# FINALIZAR
# ============================================================

def finish_search():

    global search_finished_handled

    if search_finished_handled:
        return

    search_finished_handled = True

    # Drena tudo o que restou.
    while True:

        try:
            path = result_queue.get_nowait()

        except queue.Empty:
            break

        key = str(path).casefold()

        if key not in result_keys:

            result_keys.add(key)
            results.append(path)

            if len(results) <= MAX_VISIBLE_RESULTS:
                create_result_card(path)

    elapsed = time.time() - search_started

    if stop_event.is_set():

        set_status(
            "PESQUISA INTERROMPIDA"
        )

        if progress_text is not None:
            progress_text.configure(
                text="PESQUISA INTERROMPIDA"
            )

    else:

        set_status(
            "PESQUISA CONCLUÍDA"
        )

        if progress_text is not None:
            progress_text.configure(
                text="PESQUISA CONCLUÍDA"
            )

    if start_button is not None:
        start_button.configure(
            state="normal"
        )

    if stop_button is not None:
        stop_button.configure(
            state="disabled"
        )

    # Atualização final.
    if files_stat_label is not None:

        files_stat_label.configure(
            text=(
                "ARQUIVOS\n"
                + format_number(files_scanned)
            )
        )

    if speed_stat_label is not None:

        speed = (
            files_scanned / elapsed
            if elapsed > 0
            else 0
        )

        speed_stat_label.configure(
            text=(
                "VELOCIDADE\n"
                + format_number(int(speed))
                + " /s"
            )
        )

    if time_stat_label is not None:

        time_stat_label.configure(
            text=(
                "TEMPO\n"
                + format_time(elapsed)
            )
        )

    if errors_stat_label is not None:

        errors_stat_label.configure(
            text=(
                "ERROS\n"
                + format_number(errors_count)
            )
        )

    update_search_header()

    session_history.append(
        {
            "term": search_entry.get().strip(),
            "results": matches_found,
            "files": files_scanned,
            "errors": errors_count,
            "time": format_time(elapsed),
        }
    )


# ============================================================
# INICIAR PESQUISA
# ============================================================

def start_search():

    global searching
    global search_started
    global files_scanned
    global matches_found
    global errors_count
    global stop_requested
    global search_finished_handled

    if searching:
        return

    term = search_entry.get().strip()

    if not term:

        show_dialog(
            "Pesquisa",
            "Digite um termo para iniciar a pesquisa.",
            "warning"
        )

        search_entry.focus_set()

        return

    mode = mode_var.get()

    if mode == "folder":

        if selected_folder is None:

            show_dialog(
                "Pasta não selecionada",
                "Escolha uma pasta antes de iniciar a pesquisa.",
                "warning"
            )

            return

    else:

        drives = get_windows_drives()

        if not drives:

            show_dialog(
                "Nenhum disco encontrado",
                "Não foi possível encontrar um disco disponível para pesquisa.",
                "error"
            )

            return

        confirmed = show_dialog(
            "Computador inteiro",
            (
                "Esta pesquisa poderá verificar os discos disponíveis "
                "no computador.\n\n"
                "Ela pode consumir bastante armazenamento, processador "
                "e tempo."
            ),
            "warning",
            [
                ("CANCELAR", False),
                ("CONTINUAR", True),
            ]
        )

        if not confirmed:
            return

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    clear_results()

    stop_event.clear()

    stop_requested = False
    search_finished_handled = False

    searching = True

    files_scanned = 0
    matches_found = 0
    errors_count = 0

    search_started = time.time()

    start_button.configure(
        state="disabled"
    )

    stop_button.configure(
        state="normal"
    )

    set_status(
        "PESQUISANDO"
    )

    progress_text.configure(
        text="PESQUISA EM ANDAMENTO"
    )

    search_content = bool(
        content_var.get()
    )

    thread = threading.Thread(
        target=search_worker,
        args=(
            term,
            mode,
            selected_folder,
            search_content
        ),
        daemon=True
    )

    thread.start()

    root.after(
        QUEUE_INTERVAL,
        drain_result_queue
    )

    root.after(
        STATS_INTERVAL,
        update_statistics
    )

    root.after(
        40,
        animate_progress
    )


# ============================================================
# PARAR
# ============================================================

def stop_search():

    if not searching:
        return

    stop_event.set()

    set_status(
        "SOLICITANDO PARADA"
    )

    progress_text.configure(
        text="INTERROMPENDO PESQUISA"
    )

    stop_button.configure(
        state="disabled"
    )


# ============================================================
# LIMPAR
# ============================================================

def clear_results():

    global files_scanned
    global matches_found
    global errors_count

    results.clear()
    result_keys.clear()

    files_scanned = 0
    matches_found = 0
    errors_count = 0

    if results_container is not None:

        for child in results_container.winfo_children():
            child.destroy()

    update_search_header()

    if files_stat_label is not None:
        files_stat_label.configure(
            text="ARQUIVOS\n0"
        )

    if speed_stat_label is not None:
        speed_stat_label.configure(
            text="VELOCIDADE\n0 /s"
        )

    if time_stat_label is not None:
        time_stat_label.configure(
            text="TEMPO\n00:00"
        )

    if errors_stat_label is not None:
        errors_stat_label.configure(
            text="ERROS\n0"
        )


# ============================================================
# ESCOLHER PASTA
# ============================================================

def choose_folder():

    global selected_folder

    folder = filedialog.askdirectory(
        title="PLAYER.SET.LOCATOR - Escolher pasta"
    )

    if not folder:
        return

    selected_folder = Path(folder)

    folder_label.configure(
        text=str(selected_folder),
        fg=WHITE
    )


# ============================================================
# VISUALIZADOR
# ============================================================

def view_file(path):

    try:

        if not path.exists():

            show_dialog(
                "Arquivo",
                "O arquivo não existe mais.",
                "error"
            )

            return

        size = path.stat().st_size

        if size > MAX_CONTENT_SIZE:

            show_dialog(
                "Arquivo grande",
                (
                    "O visualizador possui limite de 10 MB.\n\n"
                    "Este arquivo não será carregado."
                ),
                "warning"
            )

            return

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as file:

            content = file.read()

    except (
        PermissionError,
        OSError,
        UnicodeError
    ) as error:

        show_dialog(
            "Erro de leitura",
            f"Não foi possível ler este arquivo.\n\n{error}",
            "error"
        )

        return

    viewer = tk.Toplevel(root)

    viewer.title(
        f"{APP_NAME}  |  VISUALIZADOR"
    )

    viewer.geometry(
        "980x680"
    )

    viewer.minsize(
        700,
        500
    )

    viewer.configure(
        bg=BLACK
    )

    # Header
    header = tk.Frame(
        viewer,
        bg=BLACK
    )

    header.pack(
        fill="x",
        padx=25,
        pady=(22, 12)
    )

    tk.Label(
        header,
        text="VISUALIZADOR",
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 9, "bold")
    ).pack(
        anchor="w"
    )

    tk.Label(
        header,
        text=path.name,
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 15, "bold")
    ).pack(
        anchor="w",
        pady=(2, 0)
    )

    tk.Label(
        header,
        text=str(path.parent),
        bg=BLACK,
        fg=GRAY_DARK,
        font=("Segoe UI", 8)
    ).pack(
        anchor="w",
        pady=(2, 0)
    )

    # Editor
    editor_frame = tk.Frame(
        viewer,
        bg=BLACK_2,
        highlightbackground=BORDER_RED,
        highlightthickness=1
    )

    editor_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(0, 20)
    )

    text = tk.Text(
        editor_frame,
        bg=BLACK_2,
        fg="#D0D0D0",
        insertbackground=RED,
        selectbackground=RED_DARK_2,
        selectforeground=WHITE,
        relief="flat",
        bd=0,
        wrap="none",
        font=("Consolas", 10)
    )

    text.pack(
        side="left",
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    scrollbar = tk.Scrollbar(
        editor_frame,
        command=text.yview,
        bg=BLACK_3,
        troughcolor=BLACK,
        activebackground=RED,
        relief="flat"
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    text.configure(
        yscrollcommand=scrollbar.set
    )

    text.insert(
        "1.0",
        content
    )

    # SOMENTE LEITURA
    text.configure(
        state="disabled"
    )


# ============================================================
# TROCA DE PÁGINA
# ============================================================

def switch_page(page):

    global current_page

    pages = {
        "search": search_page,
        "files": files_page,
        "settings": settings_page,
        "about": about_page
    }

    for frame in pages.values():

        frame.pack_forget()

    pages[page].pack(
        fill="both",
        expand=True
    )

    current_page = page

    navs = {
        "search": nav_search,
        "files": nav_files,
        "settings": nav_settings,
        "about": nav_about
    }

    for button in navs.values():

        button.configure(
            bg=BLACK_3,
            fg=GRAY
        )

    navs[page].configure(
        bg=RED_DARK,
        fg=WHITE
    )

    if page == "files":
        refresh_history()


# ============================================================
# HISTÓRICO
# ============================================================

def refresh_history():

    if history_container is None:
        return

    for child in history_container.winfo_children():
        child.destroy()

    if not session_history:

        tk.Label(
            history_container,
            text="NENHUMA PESQUISA NESTA SESSÃO",
            bg=BLACK_2,
            fg=GRAY_DARK,
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=20
        )

        return

    for item in reversed(session_history):

        card = tk.Frame(
            history_container,
            bg=BLACK_3,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            fill="x",
            pady=5
        )

        tk.Frame(
            card,
            bg=RED_DARK_2,
            width=3
        ).pack(
            side="left",
            fill="y"
        )

        body = tk.Frame(
            card,
            bg=BLACK_3
        )

        body.pack(
            fill="x",
            padx=15,
            pady=12
        )

        tk.Label(
            body,
            text=item["term"],
            bg=BLACK_3,
            fg=WHITE,
            font=("Segoe UI", 10, "bold")
        ).pack(
            anchor="w"
        )

        details = (
            f'{format_number(item["results"])} resultados   |   '
            f'{format_number(item["files"])} arquivos   |   '
            f'{format_number(item["errors"])} erros   |   '
            f'{item["time"]}'
        )

        tk.Label(
            body,
            text=details,
            bg=BLACK_3,
            fg=GRAY_DARK,
            font=("Segoe UI", 8)
        ).pack(
            anchor="w",
            pady=(4, 0)
        )


# ============================================================
# RESTAURAR INTERFACE
# ============================================================

def reset_interface():

    global selected_folder

    if searching:

        show_dialog(
            "Pesquisa em andamento",
            "Pare a pesquisa antes de restaurar a interface.",
            "warning"
        )

        return

    selected_folder = None

    search_entry.delete(
        0,
        "end"
    )

    mode_var.set(
        "folder"
    )

    content_var.set(
        True
    )

    folder_label.configure(
        text="NENHUMA PASTA SELECIONADA",
        fg=GRAY_DARK
    )

    clear_results()

    set_status(
        "PRONTO"
    )

    progress_text.configure(
        text="AGUARDANDO PESQUISA"
    )


# ============================================================
# FECHAR
# ============================================================

def close_app():

    if searching:

        stop_event.set()

    root.destroy()


# ============================================================
# CONSTRUÇÃO DO HUD
# ============================================================

def build_application():

    global search_page
    global files_page
    global settings_page
    global about_page

    global search_entry
    global mode_var
    global content_var
    global folder_label

    global results_container
    global results_canvas
    global result_count_label

    global files_stat_label
    global speed_stat_label
    global time_stat_label
    global errors_stat_label

    global progress_canvas
    global progress_text

    global status_text

    global start_button
    global stop_button

    global history_container

    global nav_search
    global nav_files
    global nav_settings
    global nav_about

    clear_root()

    root.title(
        f"{APP_NAME}  |  {VERSION}"
    )

    root.geometry(
        "1180x760"
    )

    root.minsize(
        1000,
        680
    )

    root.configure(
        bg=BLACK
    )

    root.protocol(
        "WM_DELETE_WINDOW",
        close_app
    )

    # ========================================================
    # ESTRUTURA
    # ========================================================

    app = tk.Frame(
        root,
        bg=BLACK
    )

    app.pack(
        fill="both",
        expand=True
    )

    # ========================================================
    # SIDEBAR
    # ========================================================

    sidebar = tk.Frame(
        app,
        bg=BLACK_2,
        width=205
    )

    sidebar.pack(
        side="left",
        fill="y"
    )

    sidebar.pack_propagate(False)

    # Marca
    brand = tk.Frame(
        sidebar,
        bg=BLACK_2
    )

    brand.pack(
        fill="x",
        padx=22,
        pady=(28, 22)
    )

    tk.Label(
        brand,
        text="PLAYER.SET.LOCATOR",
        bg=BLACK_2,
        fg=WHITE,
        font=("Segoe UI", 11, "bold")
    ).pack(
        anchor="w"
    )

    tk.Frame(
        brand,
        bg=RED,
        height=2
    ).pack(
        fill="x",
        pady=(10, 0)
    )

    tk.Label(
        brand,
        text=f"VERSION {VERSION}",
        bg=BLACK_2,
        fg=RED_BRIGHT,
        font=("Segoe UI", 7, "bold")
    ).pack(
        anchor="w",
        pady=(7, 0)
    )

    # Linha
    tk.Frame(
        sidebar,
        bg=BORDER,
        height=1
    ).pack(
        fill="x",
        padx=18,
        pady=(0, 15)
    )

    # --------------------------------------------------------
    # NAV
    # --------------------------------------------------------

    def create_nav(
        text,
        command
    ):

        button = tk.Button(
            sidebar,
            text=text,
            command=command,
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            padx=18,
            pady=11
        )

        button.configure(
            bg=BLACK_3,
            fg=GRAY,
            activebackground=RED_DARK,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )

        button.pack(
            fill="x",
            padx=10,
            pady=2
        )

        return button

    nav_search = create_nav(
        "PESQUISA",
        lambda: switch_page("search")
    )

    nav_files = create_nav(
        "ARQUIVOS",
        lambda: switch_page("files")
    )

    nav_settings = create_nav(
        "CONFIGURAÇÕES",
        lambda: switch_page("settings")
    )

    nav_about = create_nav(
        "SOBRE",
        lambda: switch_page("about")
    )

    # Rodapé sidebar
    sidebar_bottom = tk.Frame(
        sidebar,
        bg=BLACK_2
    )

    sidebar_bottom.pack(
        side="bottom",
        fill="x",
        padx=20,
        pady=20
    )

    tk.Frame(
        sidebar_bottom,
        bg=BORDER,
        height=1
    ).pack(
        fill="x",
        pady=(0, 12)
    )

    tk.Label(
        sidebar_bottom,
        text="LOCAL SEARCH SYSTEM",
        bg=BLACK_2,
        fg=GRAY_DARK,
        font=("Segoe UI", 7, "bold")
    ).pack(
        anchor="w"
    )

    # ========================================================
    # ÁREA PRINCIPAL
    # ========================================================

    content = tk.Frame(
        app,
        bg=BLACK
    )

    content.pack(
        side="left",
        fill="both",
        expand=True
    )

    # ========================================================
    # PÁGINA PESQUISA
    # ========================================================

    search_page = tk.Frame(
        content,
        bg=BLACK
    )

    # Header
    header = tk.Frame(
        search_page,
        bg=BLACK
    )

    header.pack(
        fill="x",
        padx=30,
        pady=(27, 16)
    )

    title_box = tk.Frame(
        header,
        bg=BLACK
    )

    title_box.pack(
        side="left"
    )

    tk.Label(
        title_box,
        text="PESQUISA",
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 22, "bold")
    ).pack(
        anchor="w"
    )

    tk.Label(
        title_box,
        text="LOCALIZADOR DE ARQUIVOS",
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 8, "bold")
    ).pack(
        anchor="w",
        pady=(1, 0)
    )

    result_count_label = tk.Label(
        header,
        text="0 RESULTADOS",
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 9, "bold")
    )

    result_count_label.pack(
        side="right",
        pady=9
    )

    # ========================================================
    # CONTROLE
    # ========================================================

    control = tk.Frame(
        search_page,
        bg=BLACK_2,
        highlightbackground=BORDER_RED,
        highlightthickness=1
    )

    control.pack(
        fill="x",
        padx=30
    )

    # Linha vermelha
    tk.Frame(
        control,
        bg=RED,
        height=2
    ).pack(
        fill="x"
    )

    # Search input
    search_top = tk.Frame(
        control,
        bg=BLACK_2
    )

    search_top.pack(
        fill="x",
        padx=18,
        pady=(15, 5)
    )

    tk.Label(
        search_top,
        text="TERMO",
        bg=BLACK_2,
        fg=GRAY_DARK,
        font=("Segoe UI", 7, "bold")
    ).pack(
        anchor="w"
    )

    search_entry = tk.Entry(
        search_top,
        bg=BLACK_3,
        fg=WHITE,
        insertbackground=RED_BRIGHT,
        relief="flat",
        bd=0,
        font=("Segoe UI", 12)
    )

    search_entry.pack(
        fill="x",
        ipady=9,
        pady=(5, 0)
    )

    # --------------------------------------------------------
    # OPÇÕES
    # --------------------------------------------------------

    options = tk.Frame(
        control,
        bg=BLACK_2
    )

    options.pack(
        fill="x",
        padx=18,
        pady=10
    )

    mode_var = tk.StringVar(
        value="folder"
    )

    content_var = tk.BooleanVar(
        value=True
    )

    tk.Label(
        options,
        text="LOCAL",
        bg=BLACK_2,
        fg=GRAY_DARK,
        font=("Segoe UI", 7, "bold")
    ).pack(
        side="left",
        padx=(0, 8)
    )

    folder_radio = tk.Radiobutton(
        options,
        text="PASTA",
        variable=mode_var,
        value="folder",
        bg=BLACK_2,
        fg=WHITE,
        selectcolor=RED_DARK,
        activebackground=BLACK_2,
        activeforeground=WHITE,
        font=("Segoe UI", 8, "bold")
    )

    folder_radio.pack(
        side="left"
    )

    computer_radio = tk.Radiobutton(
        options,
        text="COMPUTADOR",
        variable=mode_var,
        value="computer",
        bg=BLACK_2,
        fg=WHITE,
        selectcolor=RED_DARK,
        activebackground=BLACK_2,
        activeforeground=WHITE,
        font=("Segoe UI", 8, "bold")
    )

    computer_radio.pack(
        side="left",
        padx=(8, 25)
    )

    content_check = tk.Checkbutton(
        options,
        text="CONTEÚDO",
        variable=content_var,
        bg=BLACK_2,
        fg=WHITE,
        selectcolor=RED_DARK,
        activebackground=BLACK_2,
        activeforeground=WHITE,
        font=("Segoe UI", 8, "bold")
    )

    content_check.pack(
        side="left"
    )

    # --------------------------------------------------------
    # PASTA
    # --------------------------------------------------------

    folder_row = tk.Frame(
        control,
        bg=BLACK_2
    )

    folder_row.pack(
        fill="x",
        padx=18,
        pady=(0, 12)
    )

    folder_label = tk.Label(
        folder_row,
        text="NENHUMA PASTA SELECIONADA",
        bg=BLACK_2,
        fg=GRAY_DARK,
        anchor="w",
        font=("Segoe UI", 8)
    )

    folder_label.pack(
        side="left",
        fill="x",
        expand=True
    )

    folder_button = tk.Button(
        folder_row,
        text="ESCOLHER PASTA",
        command=choose_folder,
        font=("Segoe UI", 8, "bold"),
        padx=15,
        pady=7
    )

    configure_button(
        folder_button
    )

    folder_button.pack(
        side="right"
    )

    # --------------------------------------------------------
    # AÇÕES
    # --------------------------------------------------------

    action_row = tk.Frame(
        control,
        bg=BLACK_2
    )

    action_row.pack(
        fill="x",
        padx=18,
        pady=(0, 17)
    )

    start_button = tk.Button(
        action_row,
        text="INICIAR PESQUISA",
        command=start_search,
        font=("Segoe UI", 8, "bold"),
        padx=20,
        pady=9
    )

    configure_button(
        start_button,
        primary=True
    )

    start_button.pack(
        side="left"
    )

    stop_button = tk.Button(
        action_row,
        text="PARAR",
        command=stop_search,
        state="disabled",
        font=("Segoe UI", 8, "bold"),
        padx=18,
        pady=9
    )

    configure_button(
        stop_button
    )

    stop_button.pack(
        side="left",
        padx=7
    )

    clear_button = tk.Button(
        action_row,
        text="LIMPAR",
        command=clear_results,
        font=("Segoe UI", 8, "bold"),
        padx=18,
        pady=9
    )

    configure_button(
        clear_button
    )

    clear_button.pack(
        side="left"
    )

    # ========================================================
    # RESULTADOS
    # ========================================================

    results_area = tk.Frame(
        search_page,
        bg=BLACK
    )

    results_area.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(17, 12)
    )

    results_header = tk.Frame(
        results_area,
        bg=BLACK
    )

    results_header.pack(
        fill="x",
        pady=(0, 7)
    )

    tk.Label(
        results_header,
        text="RESULTADOS ENCONTRADOS",
        bg=BLACK,
        fg=GRAY_DARK,
        font=("Segoe UI", 8, "bold")
    ).pack(
        side="left"
    )

    tk.Label(
        results_header,
        text="ATUALIZAÇÃO EM TEMPO REAL",
        bg=BLACK,
        fg=RED_SOFT,
        font=("Segoe UI", 7, "bold")
    ).pack(
        side="right"
    )

    result_box = tk.Frame(
        results_area,
        bg=BLACK_2,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    result_box.pack(
        fill="both",
        expand=True
    )

    results_canvas = tk.Canvas(
        result_box,
        bg=BLACK_2,
        highlightthickness=0
    )

    results_canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    result_scroll = tk.Scrollbar(
        result_box,
        command=results_canvas.yview,
        bg=BLACK_3,
        troughcolor=BLACK,
        activebackground=RED,
        relief="flat"
    )

    result_scroll.pack(
        side="right",
        fill="y"
    )

    results_canvas.configure(
        yscrollcommand=result_scroll.set
    )

    results_container = tk.Frame(
        results_canvas,
        bg=BLACK_2
    )

    results_window = results_canvas.create_window(
        (0, 0),
        window=results_container,
        anchor="nw"
    )

    def update_result_canvas(event=None):

        results_canvas.configure(
            scrollregion=results_canvas.bbox("all")
        )

        results_canvas.itemconfigure(
            results_window,
            width=results_canvas.winfo_width()
        )

    results_container.bind(
        "<Configure>",
        update_result_canvas
    )

    results_canvas.bind(
        "<Configure>",
        update_result_canvas
    )

    # ========================================================
    # PAINEL DE STATUS
    # ========================================================

    status_panel = tk.Frame(
        search_page,
        bg=BLACK
    )

    status_panel.pack(
        fill="x",
        padx=30,
        pady=(0, 15)
    )

    progress_text = tk.Label(
        status_panel,
        text="AGUARDANDO PESQUISA",
        bg=BLACK,
        fg=GRAY_DARK,
        font=("Segoe UI", 7, "bold")
    )

    progress_text.pack(
        anchor="w"
    )

    progress_canvas = tk.Canvas(
        status_panel,
        height=4,
        bg=BLACK_3,
        highlightthickness=0
    )

    progress_canvas.pack(
        fill="x",
        pady=(5, 9)
    )

    # Stats
    stats = tk.Frame(
        status_panel,
        bg=BLACK
    )

    stats.pack(
        fill="x"
    )

    def create_stat(
        parent,
        title
    ):

        box = tk.Frame(
            parent,
            bg=BLACK
        )

        box.pack(
            side="left",
            padx=(0, 40)
        )

        value = tk.Label(
            box,
            text=f"{title}\n0",
            bg=BLACK,
            fg=WHITE,
            justify="left",
            font=("Segoe UI", 8, "bold")
        )

        value.pack(
            anchor="w"
        )

        return value

    files_stat_label = create_stat(
        stats,
        "ARQUIVOS"
    )

    speed_stat_label = create_stat(
        stats,
        "VELOCIDADE"
    )

    time_stat_label = create_stat(
        stats,
        "TEMPO"
    )

    errors_stat_label = create_stat(
        stats,
        "ERROS"
    )

    # ========================================================
    # PÁGINA ARQUIVOS
    # ========================================================

    files_page = tk.Frame(
        content,
        bg=BLACK
    )

    tk.Label(
        files_page,
        text="ARQUIVOS",
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 22, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(27, 4)
    )

    tk.Label(
        files_page,
        text="HISTÓRICO DA SESSÃO",
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 8, "bold")
    ).pack(
        anchor="w",
        padx=30
    )

    history_box = tk.Frame(
        files_page,
        bg=BLACK_2,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    history_box.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=20
    )

    history_container = tk.Frame(
        history_box,
        bg=BLACK_2
    )

    history_container.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=15
    )

    # ========================================================
    # PÁGINA CONFIGURAÇÕES
    # ========================================================

    settings_page = tk.Frame(
        content,
        bg=BLACK
    )

    tk.Label(
        settings_page,
        text="CONFIGURAÇÕES",
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 22, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(27, 4)
    )

    tk.Label(
        settings_page,
        text="CONTROLE DA INTERFACE",
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 8, "bold")
    ).pack(
        anchor="w",
        padx=30
    )

    settings_box = tk.Frame(
        settings_page,
        bg=BLACK_2,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    settings_box.pack(
        fill="x",
        padx=30,
        pady=20
    )

    def settings_section(
        title,
        description
    ):

        tk.Label(
            settings_box,
            text=title,
            bg=BLACK_2,
            fg=RED_BRIGHT,
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=22,
            pady=(20, 3)
        )

        tk.Label(
            settings_box,
            text=description,
            bg=BLACK_2,
            fg=GRAY,
            justify="left",
            wraplength=750,
            font=("Segoe UI", 9)
        ).pack(
            anchor="w",
            padx=22
        )

    settings_section(
        "INTERFACE",
        "HUD em modo janela, com tema preto, vermelho e vermelho escuro."
    )

    settings_section(
        "PESQUISA",
        "A pesquisa é executada em uma thread separada para manter a interface responsiva."
    )

    settings_section(
        "VISUALIZADOR",
        "Arquivos são exibidos somente para leitura e possuem limite de 10 MB."
    )

    reset_button = tk.Button(
        settings_box,
        text="RESTAURAR INTERFACE",
        command=reset_interface,
        font=("Segoe UI", 8, "bold"),
        padx=20,
        pady=9
    )

    configure_button(
        reset_button
    )

    reset_button.pack(
        anchor="w",
        padx=22,
        pady=25
    )

    # ========================================================
    # PÁGINA SOBRE
    # ========================================================

    about_page = tk.Frame(
        content,
        bg=BLACK
    )

    tk.Label(
        about_page,
        text="SOBRE",
        bg=BLACK,
        fg=WHITE,
        font=("Segoe UI", 22, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(27, 4)
    )

    tk.Label(
        about_page,
        text=APP_NAME,
        bg=BLACK,
        fg=RED_BRIGHT,
        font=("Segoe UI", 9, "bold")
    ).pack(
        anchor="w",
        padx=30
    )

    about_box = tk.Frame(
        about_page,
        bg=BLACK_2,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    about_box.pack(
        fill="x",
        padx=30,
        pady=20
    )

    tk.Label(
        about_box,
        text=APP_NAME,
        bg=BLACK_2,
        fg=WHITE,
        font=("Segoe UI", 18, "bold")
    ).pack(
        anchor="w",
        padx=25,
        pady=(25, 3)
    )

    tk.Label(
        about_box,
        text=f"VERSION {VERSION}",
        bg=BLACK_2,
        fg=RED_BRIGHT,
        font=("Segoe UI", 8, "bold")
    ).pack(
        anchor="w",
        padx=25
    )

    tk.Frame(
        about_box,
        bg=RED,
        height=2
    ).pack(
        fill="x",
        padx=25,
        pady=18
    )

    about_text = (
        "Localizador e pesquisador de arquivos.\n\n"
        "Pesquisa por nome independentemente da extensão.\n"
        "Pesquisa de conteúdo em arquivos de texto compatíveis.\n"
        "Pesquisa em pasta selecionada ou discos disponíveis.\n"
        "Resultados em tempo real.\n"
        "Visualizador somente leitura.\n"
        "Histórico da sessão.\n"
        "Interface otimizada para uso em janela."
    )

    tk.Label(
        about_box,
        text=about_text,
        bg=BLACK_2,
        fg=GRAY,
        justify="left",
        font=("Segoe UI", 9)
    ).pack(
        anchor="w",
        padx=25,
        pady=(0, 25)
    )

    # ========================================================
    # STATUS GLOBAL
    # ========================================================

    status_bar = tk.Frame(
        root,
        bg=BLACK_2,
        height=28
    )

    status_bar.pack(
        side="bottom",
        fill="x"
    )

    status_bar.pack_propagate(False)

    tk.Frame(
        status_bar,
        bg=RED,
        width=3
    ).pack(
        side="left",
        fill="y"
    )

    status_text = tk.Label(
        status_bar,
        text="PRONTO",
        bg=BLACK_2,
        fg=RED_BRIGHT,
        anchor="w",
        font=("Segoe UI", 7, "bold")
    )

    status_text.pack(
        fill="both",
        padx=12
    )

    # ========================================================
    # INICIALIZA
    # ========================================================

    switch_page("search")

    search_entry.focus_set()


# ============================================================
# START
# ============================================================

show_terms_screen()

root.mainloop()