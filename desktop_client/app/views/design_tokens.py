"""Shared branded visual tokens and QSS for the Havaya desktop client."""

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

COLOR_BACKGROUND = "#F7F5EF"
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_ALT = "#F0F7F8"
COLOR_BORDER = "#D8DED9"
COLOR_BORDER_STRONG = "#B8C8C9"
COLOR_TEXT = "#24313A"
COLOR_TEXT_MUTED = "#65727A"
COLOR_BRAND = "#157A8A"
COLOR_BRAND_HOVER = "#0F6876"
COLOR_BRAND_PRESSED = "#0A5662"
COLOR_BRAND_SOFT = "#E5F6F8"
COLOR_ACCENT_SKY = "#5CB7D9"
COLOR_ACCENT_LEAF = "#86B84D"
COLOR_ACCENT_ORANGE = "#E49B3F"
COLOR_FOCUS = COLOR_BRAND
COLOR_SELECTED = "#DDF3F6"
COLOR_DISABLED_BACKGROUND = "#E7E4DC"
COLOR_DISABLED_TEXT = "#7B8583"
COLOR_SUCCESS, COLOR_SUCCESS_BACKGROUND = "#276B43", "#EAF6EC"
COLOR_WARNING, COLOR_WARNING_BACKGROUND = "#82520E", "#FFF2D9"
COLOR_ERROR, COLOR_ERROR_BACKGROUND = "#A8443F", "#FCEDEC"
COLOR_AI_USER_BACKGROUND = "#EAF7F8"
COLOR_AI_ASSISTANT_BACKGROUND = "#FFF7E8"
COLOR_AI_SOURCE_BACKGROUND = "#F3F8EC"


def build_branded_stylesheet() -> str:
    return f"""
QWidget {{ font-family: "Segoe UI"; font-size: {FONT_SIZE_BODY}px; color: {COLOR_TEXT}; }}
QMainWindow, QWidget#applicationRoot {{ background: {COLOR_BACKGROUND}; }}
QFrame#pageHeader, QFrame#filterPanel, QFrame#detailPanel, QFrame#loginPanel, QFrame[statCard="true"] {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; }}
#screenTitle {{ font-size: {FONT_SIZE_PAGE_TITLE}px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_TEXT}; }}
#sectionTitle {{ font-size: {FONT_SIZE_SECTION_TITLE}px; font-weight: {FONT_WEIGHT_LABEL}; color: {COLOR_TEXT}; }}
#summaryValue {{ font-size: {FONT_SIZE_SUMMARY}px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; }}
QLabel[subtitle="true"], QLabel[metadata="true"] {{ color: {COLOR_TEXT_MUTED}; }}
#sidebar {{ background: #FBFAF5; border-left: 1px solid {COLOR_BORDER}; }}
#brand {{ font-size: 19px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; }}
#sidebarEmail {{ color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_SUPPORTING}px; }}
#pageScaffold QLineEdit, #pageScaffold QComboBox, #pageScaffold QPushButton, #loginPanel QLineEdit, #loginPanel QPushButton, #sidebar QPushButton, QDialog#task20Dialog QLineEdit, QDialog#task20Dialog QPushButton {{ min-height: {CONTROL_HEIGHT_COMPACT}px; }}
#pageScaffold QLineEdit, #pageScaffold QComboBox, #loginPanel QLineEdit, QDialog#task20Dialog QLineEdit {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 0 {SPACE_2}px; }}
#pageScaffold QComboBox {{ padding-left: {SPACE_3}px; padding-right: {SPACE_2}px; }}
#pageScaffold QPushButton, #loginPanel QPushButton, #sidebar QPushButton, QDialog#task20Dialog QPushButton, QFrame#task20StatePanel QPushButton {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 0 {SPACE_3}px; background: {COLOR_SURFACE}; }}
#pageScaffold QPushButton:hover, #loginPanel QPushButton:hover, #sidebar QPushButton:hover, QDialog#task20Dialog QPushButton:hover {{ background: {COLOR_SURFACE_ALT}; }}
#pageScaffold QPushButton:focus, #pageScaffold QLineEdit:focus, #pageScaffold QComboBox:focus, #pageScaffold QTableWidget:focus, #loginPanel QPushButton:focus, #loginPanel QLineEdit:focus, #sidebar QPushButton:focus, QDialog#task20Dialog QPushButton:focus, QDialog#task20Dialog QLineEdit:focus, QDialog#task20Dialog QPlainTextEdit:focus {{ border: 2px solid {COLOR_FOCUS}; }}
#pageScaffold QPushButton:disabled, #loginPanel QPushButton:disabled, #sidebar QPushButton:disabled, QDialog#task20Dialog QPushButton:disabled {{ color: {COLOR_DISABLED_TEXT}; background: {COLOR_DISABLED_BACKGROUND}; }}
QPushButton[primary="true"], #loginPanel QPushButton[primary="true"], #pageScaffold QPushButton#customerCreateButton, #pageScaffold QPushButton#customerSearchButton, #pageScaffold QPushButton#customerEmptyActionButton, QDialog#task20Dialog QPushButton#customerDialogPrimary {{ background: {COLOR_FOCUS}; color: white; font-weight: {FONT_WEIGHT_LABEL}; }}
QPushButton[buttonRole="managementPrimary"] {{ min-height: {CONTROL_HEIGHT_COMPACT}px; padding: 0 {SPACE_3}px; background: {COLOR_BRAND}; color: white; border: 1px solid {COLOR_BRAND}; border-radius: {RADIUS_SMALL}px; font-weight: {FONT_WEIGHT_LABEL}; }}
QPushButton[buttonRole="managementPrimary"]:hover {{ background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
QPushButton[buttonRole="managementPrimary"]:pressed {{ background: {COLOR_BRAND_PRESSED}; border-color: {COLOR_BRAND_PRESSED}; }}
QPushButton[buttonRole="managementPrimary"]:disabled {{ background: {COLOR_DISABLED_BACKGROUND}; color: {COLOR_DISABLED_TEXT}; border-color: {COLOR_BORDER}; }}
QPushButton[destructive="true"] {{ color: {COLOR_ERROR}; border-color: {COLOR_ERROR}; }}
#sidebar QPushButton {{ text-align: right; color: {COLOR_TEXT}; }}
#sidebar QPushButton:hover {{ background: {COLOR_BRAND_SOFT}; border-color: {COLOR_BORDER_STRONG}; }}
#sidebar QPushButton:checked {{ background: {COLOR_BRAND}; color: white; border-color: {COLOR_BRAND}; font-weight: {FONT_WEIGHT_LABEL}; }}
QToolButton#managementRowOpenAction {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: {SPACE_1}px; }}
QToolButton#managementRowOpenAction:hover {{ background: {COLOR_SELECTED}; border-color: {COLOR_FOCUS}; }}
QToolButton#managementRowOpenAction:pressed {{ background: {COLOR_SURFACE_ALT}; }}
QLabel[feedback="success"] {{ color: {COLOR_SUCCESS}; background: {COLOR_SUCCESS_BACKGROUND}; }}
QLabel[feedback="warning"] {{ color: {COLOR_WARNING}; background: {COLOR_WARNING_BACKGROUND}; }}
QLabel[feedback="error"], #errorLabel {{ color: {COLOR_ERROR}; background: {COLOR_ERROR_BACKGROUND}; }}
QLabel[bookingState="NEW"] {{ color: {COLOR_WARNING}; background: {COLOR_WARNING_BACKGROUND}; }}
QLabel[bookingState="CONFIRMED"] {{ color: {COLOR_SUCCESS}; background: {COLOR_SUCCESS_BACKGROUND}; }}
QLabel[bookingState="COMPLETED"], QLabel[bookingState="CANCELLED"] {{ color: {COLOR_TEXT_MUTED}; background: {COLOR_SURFACE_ALT}; }}
QLabel[active="true"] {{ color: {COLOR_SUCCESS}; background: {COLOR_SUCCESS_BACKGROUND}; border-radius: 9px; padding: 3px 8px; }}
QLabel[active="false"] {{ color: {COLOR_TEXT_MUTED}; background: {COLOR_SURFACE_ALT}; border-radius: 9px; padding: 3px 8px; }}
QFrame#sharedFilterPopup {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: 12px; }}
QFrame#filterPopupSection, QFrame#filterPopupSectionHeader, QFrame#filterPopupFooter, QScrollArea#filterPopupScroll, QScrollArea#filterPopupScroll > QWidget > QWidget {{ background: transparent; border: none; }}
QFrame#filterPopupSectionHeader:hover {{ background: {COLOR_SURFACE_ALT}; border-radius: {RADIUS_SMALL}px; }}
QLabel#filterPopupSectionTitle {{ color: {COLOR_TEXT}; font-weight: {FONT_WEIGHT_LABEL}; }}
QLabel#filterPopupArrow {{ color: {COLOR_TEXT_MUTED}; }}
QFrame#filterPopupFooter {{ border-top: 1px solid {COLOR_BORDER}; }}
QFrame#sharedFilterPopup QCheckBox {{ spacing: {SPACE_2}px; }}
QFrame#sharedFilterPopup QScrollBar:vertical {{ width: 8px; background: transparent; margin: 2px; }}
QFrame#sharedFilterPopup QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 4px; min-height: 28px; }}
QFrame#sharedFilterPopup QScrollBar::add-line:vertical, QFrame#sharedFilterPopup QScrollBar::sub-line:vertical {{ height: 0; }}
QToolButton[filterChip="true"] {{ background: {COLOR_BRAND_SOFT}; color: {COLOR_BRAND}; border: 1px solid #BFE2E7; border-radius: 12px; padding: 4px 10px; }}
QFrame#assignmentCard {{ background: {COLOR_SURFACE_ALT}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; }}
QLabel[assignmentState="waiting"] {{ color: {COLOR_WARNING}; background: {COLOR_WARNING_BACKGROUND}; border-radius: 9px; padding: 3px 8px; }}
QLabel[assignmentState="assigned"] {{ color: {COLOR_SUCCESS}; background: {COLOR_SUCCESS_BACKGROUND}; border-radius: 9px; padding: 3px 8px; }}
QLabel[assignmentState="neutral"] {{ color: {COLOR_TEXT_MUTED}; background: {COLOR_SURFACE_ALT}; border-radius: 9px; padding: 3px 8px; }}
QLabel#fieldError {{ color: {COLOR_ERROR}; font-size: {FONT_SIZE_SUPPORTING}px; }}
QLineEdit[invalid="true"], QPlainTextEdit[invalid="true"] {{ border: 2px solid {COLOR_ERROR}; }}
QTableWidget[task20Table="true"] {{ background: {COLOR_SURFACE}; alternate-background-color: {COLOR_SURFACE_ALT}; gridline-color: {COLOR_BORDER}; }}
QTableWidget[task20Table="true"] QHeaderView::section {{ background: #EDF6F6; color: {COLOR_TEXT}; border: none; border-bottom: 1px solid {COLOR_BORDER_STRONG}; padding: {TABLE_CELL_PADDING_Y}px {TABLE_CELL_PADDING_X}px; font-weight: {FONT_WEIGHT_LABEL}; }}
QTableWidget[task20Table="true"]::item {{ padding: {TABLE_CELL_PADDING_Y}px {TABLE_CELL_PADDING_X}px; }}
QTableWidget[task20Table="true"]::item:selected {{ background: {COLOR_SELECTED}; color: {COLOR_TEXT}; }}
QFrame[aiMessage="user"] {{ background: {COLOR_AI_USER_BACKGROUND}; border: 1px solid #C9E9ED; border-radius: {RADIUS_MEDIUM}px; }}
QFrame[aiMessage="assistant"] {{ background: {COLOR_AI_ASSISTANT_BACKGROUND}; border: 1px solid #F1D8AA; border-radius: {RADIUS_MEDIUM}px; }}
QFrame[aiSource="true"] {{ background: {COLOR_AI_SOURCE_BACKGROUND}; border: 1px solid #D8E8C9; border-radius: {RADIUS_SMALL}px; }}
"""


def build_neutral_stylesheet() -> str:
    """Backward-compatible name for the now-branded global stylesheet."""
    return build_branded_stylesheet()
