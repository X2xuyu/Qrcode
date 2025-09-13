import re
import qrcode
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# color
HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")
def safe_color(c: str, fallback: str = "#1e1e2e") -> str:
    return c if isinstance(c, str) and HEX6.match(c) else fallback

def darken(hex_color: str, factor: float = 0.85) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


BG      = safe_color("#1e1e2e")   # bg
CARD    = safe_color("#2e2e3e")   # card
FG      = safe_color("#ffffff")   # txt
ACCENT  = safe_color("#4caf50")   # Generate
PRIMARY = safe_color("#2196f3")   # Save
DANGER  = safe_color("#ef4444")   # Clear

QR_SIZE = 320


def make_hover(btn: tk.Button, normal_bg: str):
    hover_bg = darken(normal_bg, 0.85)   
    btn.config(cursor="hand2", bg=normal_bg, activebackground=hover_bg)
    def _in(_):  btn.configure(bg=hover_bg)
    def _out(_): btn.configure(bg=normal_bg)
    btn.bind("<Enter>", _in)
    btn.bind("<Leave>", _out)


class QRApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Link → QR Code")
        self.root.geometry("560x720")
        self.root.minsize(520, 640)
        self.root.configure(bg=BG)

        
        tk.Label(root, text="Link → QR Code",
                 font=("Segoe UI", 20, "bold"), fg=FG, bg=BG).pack(pady=(18, 8))
        tk.Label(root, text="Generate QR",
                 font=("Segoe UI", 10), fg="#cbd5e1", bg=BG).pack(pady=(0, 14))

       
        card = tk.Frame(root, bg=CARD, bd=0, highlightthickness=0)
        card.pack(fill="x", padx=24, pady=8)

        tk.Label(card, text="Link / URL", font=("Segoe UI", 10, "bold"),
                 fg=FG, bg=CARD).pack(anchor="w", padx=16, pady=(16, 6))
        self.url = tk.StringVar()
        entry = tk.Entry(card, textvariable=self.url, font=("Segoe UI", 12),
                         bg=BG, fg=FG, insertbackground=FG, relief="flat")
        entry.pack(fill="x", padx=16, pady=(0, 16), ipady=8)
        entry.focus_set()

        
        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        gen_btn = tk.Button(btn_row, text="Generate QR", font=("Segoe UI", 10, "bold"),
                            bg=ACCENT, fg="white", relief="flat",
                            padx=14, pady=8, command=self.generate)
        gen_btn.pack(side="left")
        make_hover(gen_btn, ACCENT)

        save_btn = tk.Button(btn_row, text="Save PNG", font=("Segoe UI", 10, "bold"),
                             bg=PRIMARY, fg="white", relief="flat",
                             padx=14, pady=8, command=self.save)
        save_btn.pack(side="left", padx=10)
        make_hover(save_btn, PRIMARY)

        clear_btn = tk.Button(btn_row, text="Clear", font=("Segoe UI", 10, "bold"),
                              bg=DANGER, fg="white", relief="flat",
                              padx=14, pady=8, command=self.clear)
        clear_btn.pack(side="right")
        make_hover(clear_btn, DANGER)

    
        prev_card = tk.Frame(root, bg=CARD, bd=0, highlightthickness=0)
        prev_card.pack(fill="both", expand=True, padx=24, pady=8)
        tk.Label(prev_card, text="Preview", font=("Segoe UI", 10, "bold"),
                 fg=FG, bg=CARD).pack(anchor="w", padx=16, pady=(16, 8))
        self.canvas = tk.Label(prev_card, bg=CARD)
        self.canvas.pack(padx=16, pady=(0, 16), expand=True)

        
        self.qr_pil = None
        self.qr_tk = None

        
        tk.Label(root, text="© link2qr • made with Python + Tkinter by daxk",
                 font=("Segoe UI", 9), fg="#94a3b8", bg=BG).pack(pady=(0, 10))

    def generate(self):
        url = (self.url.get() or "").strip()
        if not url:
            messagebox.showwarning("Hey", "Paste link first!")
            return

        qr = qrcode.QRCode(
            version=None, box_size=10, border=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img = img.resize((QR_SIZE, QR_SIZE))

        self.qr_pil = img
        self.qr_tk = ImageTk.PhotoImage(img)
        self.canvas.configure(image=self.qr_tk)

    def save(self):
        if self.qr_pil is None:
            messagebox.showinfo("Not yet created", "Press Generate before saving")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            title="Save file QR"
        )
        if path:
            self.qr_pil.save(path)
            messagebox.showinfo("success", f"Saved:\n{path}")

    def clear(self):
        self.url.set("")
        self.qr_pil = None
        self.qr_tk = None
        self.canvas.configure(image="", text="")


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG)
    app = QRApp(root)
    root.mainloop()
