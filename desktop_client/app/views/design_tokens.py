"""Temporary neutral Task 20 UI tokens; these are not product branding."""

SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_6, SPACE_8 = 4, 8, 12, 16, 24, 32
CONTROL_HEIGHT_COMPACT, CONTROL_HEIGHT, CONTROL_HEIGHT_LARGE = 32, 40, 44
ICON_SIZE_SMALL, ICON_SIZE, ICON_SIZE_LARGE = 16, 20, 24
RADIUS_SMALL, RADIUS_MEDIUM, RADIUS_LARGE = 4, 8, 12
DURATION_INSTANT, DURATION_FAST, DURATION_STANDARD = 0, 120, 200
DIALOG_WIDTH_DEFAULT, DIALOG_WIDTH_MAX = 520, 720
DIALOG_PADDING, DIALOG_ROW_GAP, DIALOG_SECTION_GAP = 24, 12, 24
TABLE_CELL_PADDING_X, TABLE_CELL_PADDING_Y = 12, 8
TABLE_ROW_HEIGHT, TABLE_HEADER_HEIGHT = 40, 40
TABLE_MIN_WIDTH, DETAIL_MIN_WIDTH = 360, 300
TABLE_COLUMN_PRIMARY_MIN = 110
TABLE_COLUMN_SECONDARY_MIN = 75
TABLE_COLUMN_TECHNICAL_MIN = 100
TABLE_COLUMN_COMPACT_MIN = 70
TABLE_COLUMN_ACTION_MIN = 80
FONT_SIZE_SUPPORTING, FONT_SIZE_BODY = 12, 14
FONT_SIZE_SECTION_TITLE, FONT_SIZE_PAGE_TITLE, FONT_SIZE_SUMMARY = 18, 24, 26
FONT_WEIGHT_NORMAL, FONT_WEIGHT_LABEL, FONT_WEIGHT_TITLE = 400, 600, 700
ELEVATION_NONE = (0, 0, 0, 0)
ELEVATION_LOW = (0, 1, 3, 12)
ELEVATION_MODAL = (0, 8, 24, 18)

COLOR_BACKGROUND = "#F5F6F8"
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_ALT = "#EEF1F4"
COLOR_BORDER = "#C8CDD4"
COLOR_TEXT = "#1F2933"
COLOR_TEXT_MUTED = "#5F6B76"
COLOR_FOCUS = "#1F6FEB"
COLOR_SELECTED = "#DCEBFF"
COLOR_DISABLED_BACKGROUND = "#E5E7EB"
COLOR_DISABLED_TEXT = "#7A858F"
COLOR_SUCCESS, COLOR_SUCCESS_BACKGROUND = "#176B45", "#E7F5ED"
COLOR_WARNING, COLOR_WARNING_BACKGROUND = "#7A4D00", "#FFF4D6"
COLOR_ERROR, COLOR_ERROR_BACKGROUND = "#A61B1B", "#FDECEC"


def build_neutral_stylesheet() -> str:
    return f"""
QWidget {{ font-size: {FONT_SIZE_BODY}px; color: {COLOR_TEXT}; }}
QMainWindow, QWidget#applicationRoot {{ background: {COLOR_BACKGROUND}; }}
QFrame#pageHeader, QFrame#filterPanel, QFrame#detailPanel, QFrame#loginPanel {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; }}
#screenTitle {{ font-size: {FONT_SIZE_PAGE_TITLE}px; font-weight: {FONT_WEIGHT_TITLE}; }}
#sectionTitle {{ font-size: {FONT_SIZE_SECTION_TITLE}px; font-weight: {FONT_WEIGHT_LABEL}; }}
#summaryValue {{ font-size: {FONT_SIZE_SUMMARY}px; font-weight: {FONT_WEIGHT_TITLE}; }}
#sidebar {{ background: {COLOR_SURFACE}; border-left: 1px solid {COLOR_BORDER}; }}
#brand {{ font-size: 20px; font-weight: {FONT_WEIGHT_TITLE}; }}
#pageScaffold QLineEdit, #pageScaffold QComboBox, #pageScaffold QPushButton, #loginPanel QLineEdit, #loginPanel QPushButton, #sidebar QPushButton, QDialog#task20Dialog QLineEdit, QDialog#task20Dialog QPushButton {{ min-height: {CONTROL_HEIGHT_COMPACT}px; }}
#pageScaffold QLineEdit, #pageScaffold QComboBox, #loginPanel QLineEdit, QDialog#task20Dialog QLineEdit {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 0 {SPACE_2}px; }}
#pageScaffold QPushButton, #loginPanel QPushButton, #sidebar QPushButton, QDialog#task20Dialog QPushButton, QFrame#task20StatePanel QPushButton {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 0 {SPACE_3}px; background: {COLOR_SURFACE}; }}
#pageScaffold QPushButton:hover, #loginPanel QPushButton:hover, #sidebar QPushButton:hover, QDialog#task20Dialog QPushButton:hover {{ background: {COLOR_SURFACE_ALT}; }}
#pageScaffold QPushButton:focus, #pageScaffold QLineEdit:focus, #pageScaffold QComboBox:focus, #pageScaffold QTableWidget:focus, #loginPanel QPushButton:focus, #loginPanel QLineEdit:focus, #sidebar QPushButton:focus, QDialog#task20Dialog QPushButton:focus, QDialog#task20Dialog QLineEdit:focus, QDialog#task20Dialog QPlainTextEdit:focus {{ border: 2px solid {COLOR_FOCUS}; }}
#pageScaffold QPushButton:disabled, #loginPanel QPushButton:disabled, #sidebar QPushButton:disabled, QDialog#task20Dialog QPushButton:disabled {{ color: {COLOR_DISABLED_TEXT}; background: {COLOR_DISABLED_BACKGROUND}; }}
QPushButton[primary="true"], #loginPanel QPushButton[primary="true"], #pageScaffold QPushButton#customerCreateButton, #pageScaffold QPushButton#customerSearchButton, QDialog#task20Dialog QPushButton#customerDialogPrimary {{ background: {COLOR_FOCUS}; color: white; font-weight: {FONT_WEIGHT_LABEL}; }}
QPushButton[destructive="true"] {{ color: {COLOR_ERROR}; border-color: {COLOR_ERROR}; }}
QLabel[feedback="success"] {{ color: {COLOR_SUCCESS}; background: {COLOR_SUCCESS_BACKGROUND}; }}
QLabel[feedback="warning"] {{ color: {COLOR_WARNING}; background: {COLOR_WARNING_BACKGROUND}; }}
QLabel[feedback="error"], #errorLabel {{ color: {COLOR_ERROR}; background: {COLOR_ERROR_BACKGROUND}; }}
QTableWidget[task20Table="true"] {{ background: {COLOR_SURFACE}; alternate-background-color: {COLOR_SURFACE_ALT}; gridline-color: {COLOR_BORDER}; }}
QTableWidget[task20Table="true"]::item {{ padding: {TABLE_CELL_PADDING_Y}px {TABLE_CELL_PADDING_X}px; }}
QTableWidget[task20Table="true"]::item:selected {{ background: {COLOR_SELECTED}; color: {COLOR_TEXT}; }}
"""
