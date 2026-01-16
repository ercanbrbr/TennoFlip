def get_styles(theme="dark"):
    if theme == "dark":
        colors = {
            "window_bg": "#0d1117",
            "widget_bg": "#0d1117",
            "topbar_bg": "#161b22",
            "border": "#30363d",
            "text_main": "#c9d1d9",
            "text_header": "#f0f6fc",
            "text_muted": "#8b949e",
            "accent": "#58a6ff",
            "accent_hover": "#1f6feb",
            "button_bg": "#21262d",
            "button_hover": "#30363d",
            "primary": "#238636",
            "primary_hover": "#2ea043",
            "item_selected": "#21262d"
        }
    else: 
        colors = {
            "window_bg": "#f6f8fa",
            "widget_bg": "#ffffff",
            "topbar_bg": "#f6f8fa",
            "border": "#d0d7de",
            "text_main": "#24292f",
            "text_header": "#24292f",
            "text_muted": "#57606a",
            "accent": "#0969da",
            "accent_hover": "#0550ae",
            "button_bg": "#f3f4f6",
            "button_hover": "#ebecf0",
            "primary": "#1a7f37",
            "primary_hover": "#116329",
            "item_selected": "#f6f8fa"
        }

    return f"""
    QMainWindow, QDialog {{
        background-color: {colors['window_bg']};
    }}
    
    QWidget#main_container {{
        background-color: {colors['window_bg']};
    }}

    QStackedWidget {{
        background-color: transparent;
    }}
    
    ItemTableWidget, ArcanePacksWidget {{
        background-color: transparent;
    }}
    
    QTableWidget {{
        background-color: {colors['widget_bg']};
        border: 1px solid {colors['border']};
        gridline-color: {colors['border']};
        border-radius: 4px;
        outline: none;
    }}
    
    QWidget {{
        color: {colors['text_main']};
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-size: 13px;
        outline: none;
    }}

    QWidget#topbar_container {{
        background-color: {colors['topbar_bg']};
    }}
    QPushButton#theme_toggle {{
        background-color: transparent;
        border: none;
        font-size: 16px;
        padding: 0;
    }}
    QPushButton#theme_toggle:hover {{
        background-color: {colors['button_hover']};
        border-radius: 16px;
    }}
    QListWidget#topbar {{
        background-color: {colors['topbar_bg']};
        border: none;
        border-bottom: 1px solid {colors['border']};
        outline: none;
        padding: 0px 10px;
    }}
    QListWidget#topbar::item {{
        height: 40px;
        padding: 0px 20px;
        border-radius: 0px;
        margin: 0px;
    }}
    QListWidget#topbar::item:hover {{
        background-color: {colors['button_hover']};
    }}
    QListWidget#topbar::item:selected {{
        background-color: transparent;
        color: {colors['accent']};
        border-bottom: 2px solid {colors['accent']};
        font-weight: bold;
    }}

    QTableWidget::item:selected {{
        background-color: {colors['item_selected']};
        color: {colors['text_header']};
    }}
    QHeaderView::section {{
        background-color: {colors['topbar_bg']};
        color: {colors['text_muted']};
        padding: 6px;
        border: none;
        border-bottom: 1px solid {colors['border']};
        border-right: 1px solid {colors['border']};
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
    }}
    
    QScrollBar:vertical {{
        border: none;
        background: {colors['window_bg']};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {colors['border']};
        min-height: 20px;
        border-radius: 5px;
    }}

    QLineEdit {{
        background-color: {colors['widget_bg']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 5px 10px;
        color: {colors['text_header']};
    }}
    QLineEdit:focus {{
        border: 1px solid {colors['accent']};
    }}

    QPushButton {{
        background-color: {colors['button_bg']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 6px 16px;
        color: {colors['text_main']};
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {colors['button_hover']};
    }}
    QPushButton#primary_action {{
        background-color: {colors['primary']};
        border: 1px solid {colors['primary']};
        color: #ffffff;
    }}
    QPushButton#primary_action:hover {{
        background-color: {colors['primary_hover']};
    }}
    QPushButton:checked {{
        background-color: {colors['button_hover']};
        border: 1px solid {colors['accent']};
        color: {colors['accent']};
    }}
    QPushButton#toggle_left {{
        border-top-right-radius: 0px;
        border-bottom-right-radius: 0px;
        border-right: none;
    }}
    QPushButton#toggle_right {{
        border-top-left-radius: 0px;
        border-bottom-left-radius: 0px;
    }}
    QPushButton#toggle_left:checked, QPushButton#toggle_right:checked {{
        background-color: {colors['accent']};
        border: 1px solid {colors['accent']};
        color: #ffffff;
    }}

    QLabel#header {{
        font-size: 18px;
        font-weight: bold;
        color: {colors['text_header']};
    }}
    """

def get_main_style():
    return get_styles("dark")
