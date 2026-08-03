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
QWidget {{ font-family: "Segoe UI", "Arial", "Tahoma"; font-size: {FONT_SIZE_BODY}px; color: {COLOR_TEXT}; }}
QMainWindow, QWidget#applicationRoot {{ background: {COLOR_BACKGROUND}; }}
QFrame#pageHeader, QFrame#filterPanel, QFrame#detailPanel, QFrame#loginPanel, QFrame[statCard="true"] {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; }}
#screenTitle {{ font-size: {FONT_SIZE_PAGE_TITLE}px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_TEXT}; }}
#sectionTitle {{ font-size: {FONT_SIZE_SECTION_TITLE}px; font-weight: {FONT_WEIGHT_LABEL}; color: {COLOR_TEXT}; }}
#summaryValue {{ font-size: {FONT_SIZE_SUMMARY}px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; }}
QLabel[subtitle="true"], QLabel[metadata="true"] {{ color: {COLOR_TEXT_MUTED}; }}
QWidget#dashboardPage {{ background: {COLOR_BACKGROUND}; }}
QFrame#dashboardHero {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; background: {COLOR_SURFACE}; }}
QLabel#dashboardHeroTitle {{ font-size: 30px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; background: transparent; }}
QLabel#dashboardHeroSubtitle {{ font-size: {FONT_SIZE_BODY}px; color: {COLOR_TEXT_MUTED}; background: transparent; }}
QFrame#dashboardStatCard {{ border-top-width: 2px; min-height: 128px; }}
QFrame#dashboardStatCard[accent="sky"] {{ border-top-color: {COLOR_ACCENT_SKY}; }}
QFrame#dashboardStatCard[accent="green"] {{ border-top-color: {COLOR_ACCENT_LEAF}; }}
QFrame#dashboardStatCard[accent="orange"] {{ border-top-color: {COLOR_ACCENT_ORANGE}; }}
QFrame#dashboardStatCard[accent="coral"] {{ border-top-color: {COLOR_ERROR}; }}
QLabel#dashboardStatLabel {{ font-weight: {FONT_WEIGHT_LABEL}; color: {COLOR_TEXT}; }}
QPushButton#dashboardDrillButton {{ min-height: 34px; background: {COLOR_SURFACE_ALT}; border-radius: {RADIUS_SMALL}px; font-weight: {FONT_WEIGHT_LABEL}; }}
QPushButton#dashboardDrillButton[accent="sky"] {{ color: {COLOR_BRAND}; border-color: #BFE2E7; }}
QPushButton#dashboardDrillButton[accent="green"] {{ color: {COLOR_SUCCESS}; border-color: #C9E7C5; }}
QPushButton#dashboardDrillButton[accent="orange"] {{ color: {COLOR_WARNING}; border-color: #F0D5A4; }}
QPushButton#dashboardDrillButton[accent="coral"] {{ color: {COLOR_ERROR}; border-color: #EDC4C1; }}
QFrame#dashboardShortcuts, QFrame#dashboardSection {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; }}
QPushButton#dashboardShortcutButton {{ min-height: 42px; background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; font-weight: {FONT_WEIGHT_LABEL}; }}
QPushButton#dashboardShortcutButton:hover {{ background: {COLOR_BRAND_SOFT}; border-color: {COLOR_BORDER_STRONG}; }}
QPushButton#dashboardShortcutButton[buttonRole="managementPrimary"] {{ background: {COLOR_BRAND}; color: white; border-color: {COLOR_BRAND}; }}
QPushButton#dashboardShortcutButton[buttonRole="managementPrimary"]:hover {{ background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
QLabel#dashboardSectionTitle {{ font-size: {FONT_SIZE_SECTION_TITLE}px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; }}
QWidget#customersHero {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; background: {COLOR_SURFACE}; }}
QWidget#customersHero QLabel[customersHeroTitle="true"] {{ font-size: 32px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; background: transparent; }}
QWidget#customersHero QLabel[customersHeroSubtitle="true"] {{ font-size: 15px; font-weight: {FONT_WEIGHT_LABEL}; color: {COLOR_TEXT}; background: transparent; }}
QWidget#customersHero QPushButton#customerCreateButton {{ min-height: 40px; padding: 0 {SPACE_4}px; }}
QFrame[customersHeader="true"] QLabel#screenTitle {{ color: {COLOR_BRAND}; }}
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
QDialog#task20Dialog {{ background: {COLOR_BACKGROUND}; }}
QDialog#task20Dialog QLabel[dialogLead="true"] {{ color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px; }}
QDialog#task20Dialog QLabel[dialogHint="true"] {{ color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_SUPPORTING}px; }}
QDialog#task20Dialog QScrollArea#dialogScrollArea, QDialog#task20Dialog QScrollArea#dialogScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QDialog#task20Dialog QFrame[dialogSection="true"] {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; }}
QDialog#task20Dialog QLabel[dialogSectionTitle="true"] {{ color: {COLOR_BRAND}; font-size: {FONT_SIZE_SECTION_TITLE}px; font-weight: {FONT_WEIGHT_TITLE}; }}
QDialog#task20Dialog QLabel[dialogFieldLabel="true"] {{ color: {COLOR_TEXT}; font-weight: {FONT_WEIGHT_LABEL}; padding: 0 {SPACE_1}px; }}
QDialog#task20Dialog QLineEdit, QDialog#task20Dialog QPlainTextEdit {{ background: {COLOR_SURFACE}; color: {COLOR_TEXT}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 8px {SPACE_2}px; selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; text-align: right; }}
QDialog#task20Dialog QComboBox, QDialog#task20Dialog QSpinBox, QDialog#task20Dialog QDoubleSpinBox, QDialog#task20Dialog QDateTimeEdit, QDialog#task20Dialog QTextEdit {{ background: {COLOR_SURFACE}; color: {COLOR_TEXT}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 6px {SPACE_2}px; selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; }}
QDialog#task20Dialog QComboBox:focus, QDialog#task20Dialog QSpinBox:focus, QDialog#task20Dialog QDoubleSpinBox:focus, QDialog#task20Dialog QDateTimeEdit:focus, QDialog#task20Dialog QTextEdit:focus {{ color: {COLOR_TEXT}; selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; border: 2px solid {COLOR_FOCUS}; }}
QDialog#task20Dialog QLineEdit:hover, QDialog#task20Dialog QPlainTextEdit:hover {{ color: {COLOR_TEXT}; border-color: {COLOR_BORDER_STRONG}; }}
QDialog#task20Dialog QLineEdit:focus, QDialog#task20Dialog QPlainTextEdit:focus {{ color: {COLOR_TEXT}; selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; border: 2px solid {COLOR_FOCUS}; }}
QDialog#task20Dialog QLineEdit[readOnly="true"] {{ background: #F6F8F8; color: {COLOR_TEXT_MUTED}; selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; }}
QDialog#task20Dialog QPlainTextEdit {{ min-height: 120px; }}
QDialog#task20Dialog QLabel[dialogStaticValue="true"] {{ background: #F8FBFB; color: {COLOR_TEXT}; border: 1px solid #E4ECEB; border-radius: {RADIUS_SMALL}px; padding: 8px {SPACE_2}px; }}
QDialog#task20Dialog QDialogButtonBox#dialogButtonBox {{ background: transparent; }}
QDialog#task20Dialog QDialogButtonBox#dialogButtonBox QPushButton {{ min-width: 140px; min-height: {CONTROL_HEIGHT_LARGE}px; border-radius: {RADIUS_SMALL}px; }}
QDialog#task20Dialog QPushButton#customerDialogPrimary:hover {{ background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
QDialog#task20Dialog QPushButton#customerDialogPrimary:pressed {{ background: {COLOR_BRAND_PRESSED}; border-color: {COLOR_BRAND_PRESSED}; }}

/* Customer details: scoped so no other management screen changes. */
QWidget#customerDetailsPage {{ background: transparent; }}
QScrollArea#customerDetailsScroll,
QScrollArea#customerDetailsScroll > QWidget > QWidget,
QWidget#customerDetailsCanvas {{ background: transparent; border: none; }}
QPushButton#customerBackButton {{
    min-height: 38px;
    padding: 0 {SPACE_4}px;
    color: {COLOR_BRAND};
    background: {COLOR_SURFACE};
    border: 1px solid #BFDDE1;
    border-radius: {RADIUS_MEDIUM}px;
    font-weight: {FONT_WEIGHT_LABEL};
    text-align: right;
}}
QPushButton#customerBackButton:hover {{ background: {COLOR_BRAND_SOFT}; border-color: {COLOR_BRAND}; }}
QPushButton#customerBackButton:pressed {{ background: {COLOR_SELECTED}; }}
QFrame[customerDetailHeader="true"] {{
    min-height: 156px;
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-right: 4px solid {COLOR_BRAND};
    border-radius: {RADIUS_LARGE}px;
}}
QFrame[customerDetailHeader="true"] QLabel#customerDetailTitle {{
    font-size: 28px;
    font-weight: {FONT_WEIGHT_TITLE};
    color: {COLOR_TEXT};
    background: transparent;
}}
QFrame[customerDetailHeader="true"] QLabel#customerDetailSubtitle {{
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_SIZE_BODY}px;
    background: transparent;
}}
QFrame[customerDetailHeader="true"] QLabel#customerDetailStatus {{
    min-width: 58px;
    max-width: 88px;
    font-weight: {FONT_WEIGHT_LABEL};
}}
QWidget#customerDetailActions QPushButton {{
    min-height: 40px;
    border-radius: {RADIUS_MEDIUM}px;
    font-weight: {FONT_WEIGHT_LABEL};
}}
QPushButton[customerDetailAction="edit"] {{
    color: white;
    background: {COLOR_BRAND};
    border: 1px solid {COLOR_BRAND};
}}
QPushButton[customerDetailAction="edit"]:hover {{ background: {COLOR_BRAND_HOVER}; border-color: {COLOR_BRAND_HOVER}; }}
QPushButton[customerDetailAction="edit"]:pressed {{ background: {COLOR_BRAND_PRESSED}; border-color: {COLOR_BRAND_PRESSED}; }}
QPushButton[customerDetailAction="password"] {{
    color: {COLOR_TEXT};
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER_STRONG};
}}
QPushButton[customerDetailAction="password"]:hover {{ background: {COLOR_SURFACE_ALT}; border-color: {COLOR_BRAND}; }}
QPushButton[customerDetailAction="deactivate"] {{
    color: {COLOR_ERROR};
    background: {COLOR_SURFACE};
    border: 1px solid #E6B8B5;
}}
QPushButton[customerDetailAction="deactivate"]:hover {{ background: {COLOR_ERROR_BACKGROUND}; border-color: {COLOR_ERROR}; }}
QPushButton[customerDetailAction="reactivate"] {{
    color: {COLOR_SUCCESS};
    background: {COLOR_SUCCESS_BACKGROUND};
    border: 1px solid #BFDDBF;
}}
QPushButton[customerDetailAction="reactivate"]:hover {{ border-color: {COLOR_SUCCESS}; }}
QFrame[customerDetailCard="true"] {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_LARGE}px;
}}
QFrame[customerDetailCard="true"][customerDetailCardRole="primary"] {{ border-right: 4px solid {COLOR_BRAND}; }}
QFrame[customerDetailCard="true"][customerDetailCardRole="contact"] {{ border-right: 4px solid {COLOR_ACCENT_SKY}; }}
QFrame[customerDetailCard="true"][customerDetailCardRole="system"] {{ border-right: 4px solid {COLOR_ACCENT_LEAF}; }}
QFrame[customerDetailCard="true"] QLabel#sectionTitle {{
    color: {COLOR_BRAND};
    font-size: 20px;
    font-weight: {FONT_WEIGHT_TITLE};
    background: transparent;
}}
QFrame[customerDetailCard="true"] QLabel[customerDetailFieldLabel="true"] {{
    color: {COLOR_TEXT_MUTED};
    font-weight: {FONT_WEIGHT_LABEL};
    background: transparent;
    padding: 0 {SPACE_1}px;
}}
QFrame[customerDetailCard="true"] QLabel[customerDetailFieldValue="true"] {{
    min-height: 36px;
    color: {COLOR_TEXT};
    background: #F8FBFB;
    border: 1px solid #E4ECEB;
    border-radius: {RADIUS_SMALL}px;
    padding: 6px {SPACE_3}px;
}}
/* Shared management screens: same approved visual language as Customers. */
QWidget#managementHero {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; background: {COLOR_SURFACE}; }}
QWidget#managementHero QLabel[managementHeroTitle="true"] {{ font-size: 32px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_BRAND}; background: transparent; }}
QWidget#managementHero QLabel[managementHeroSubtitle="true"] {{ font-size: 15px; font-weight: {FONT_WEIGHT_LABEL}; color: {COLOR_TEXT}; background: transparent; }}
QWidget#managementHero QPushButton[managementHeroAction="true"] {{ min-height: 40px; padding: 0 {SPACE_4}px; }}
QWidget#managementDetailsPage {{ background: transparent; }}
QScrollArea#managementDetailsScroll,
QScrollArea#managementDetailsScroll > QWidget > QWidget,
QWidget#managementDetailsCanvas {{ background: transparent; border: none; }}
QFrame[managementDetailHeader="true"] {{
    min-height: 156px;
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-right: 4px solid {COLOR_BRAND};
    border-radius: {RADIUS_LARGE}px;
}}
QFrame[managementDetailHeader="true"] QLabel#managementDetailTitle {{
    font-size: 28px;
    font-weight: {FONT_WEIGHT_TITLE};
    color: {COLOR_TEXT};
    background: transparent;
}}
QFrame[managementDetailHeader="true"] QLabel#managementDetailSubtitle {{ color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px; background: transparent; }}
QFrame[managementDetailHeader="true"] QLabel#managementDetailStatus {{ min-width: 58px; max-width: 100px; font-weight: {FONT_WEIGHT_LABEL}; }}
QWidget#managementDetailActions QPushButton {{ min-height: 40px; border-radius: {RADIUS_MEDIUM}px; font-weight: {FONT_WEIGHT_LABEL}; }}
QFrame[managementDetailCard="true"] {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_LARGE}px; }}
QFrame[managementDetailCard="true"][managementDetailCardRole="primary"] {{ border-right: 4px solid {COLOR_BRAND}; }}
QFrame[managementDetailCard="true"][managementDetailCardRole="secondary"] {{ border-right: 4px solid {COLOR_ACCENT_SKY}; }}
QFrame[managementDetailCard="true"][managementDetailCardRole="system"] {{ border-right: 4px solid {COLOR_ACCENT_LEAF}; }}
QFrame[managementDetailCard="true"] QLabel#sectionTitle {{ color: {COLOR_BRAND}; font-size: 20px; font-weight: {FONT_WEIGHT_TITLE}; background: transparent; }}
QFrame[managementDetailCard="true"] QLabel[managementDetailFieldLabel="true"] {{ color: {COLOR_TEXT_MUTED}; font-weight: {FONT_WEIGHT_LABEL}; background: transparent; padding: 0 {SPACE_1}px; }}
QFrame[managementDetailCard="true"] QLabel[managementDetailFieldValue="true"] {{ min-height: 36px; color: {COLOR_TEXT}; background: #F8FBFB; border: 1px solid #E4ECEB; border-radius: {RADIUS_SMALL}px; padding: 6px {SPACE_3}px; }}
QFrame[managementExtraPanel="true"] {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_LARGE}px; }}
QFrame[managementExtraPanel="true"] QLabel#sectionTitle {{ color: {COLOR_BRAND}; font-size: 20px; font-weight: {FONT_WEIGHT_TITLE}; }}
QTableWidget[managementReferenceTable="true"] {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; background: {COLOR_SURFACE}; alternate-background-color: {COLOR_SURFACE_ALT}; gridline-color: {COLOR_BORDER}; }}
QTableWidget[managementReferenceTable="true"] QHeaderView::section {{ background: #F2F9F8; color: {COLOR_BRAND}; border: none; border-bottom: 1px solid {COLOR_BORDER_STRONG}; padding: {TABLE_CELL_PADDING_Y}px {TABLE_CELL_PADDING_X}px; font-weight: {FONT_WEIGHT_LABEL}; }}
QTableWidget[managementReferenceTable="true"]::item {{ padding: {TABLE_CELL_PADDING_Y}px {TABLE_CELL_PADDING_X}px; }}
QTableWidget[managementReferenceTable="true"]::item:selected {{ background: {COLOR_SELECTED}; color: {COLOR_TEXT}; }}

#sidebar QPushButton {{ text-align: right; color: {COLOR_TEXT}; }}
#sidebar QPushButton:hover {{ background: {COLOR_BRAND_SOFT}; border-color: {COLOR_BORDER_STRONG}; }}
#sidebar QPushButton:checked {{ background: {COLOR_BRAND}; color: white; border-color: {COLOR_BRAND}; font-weight: {FONT_WEIGHT_LABEL}; }}
QPushButton[summaryQueue] {{ background: {COLOR_SURFACE}; color: {COLOR_TEXT}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; padding: {SPACE_2}px {SPACE_4}px; font-weight: {FONT_WEIGHT_LABEL}; text-align: right; }}
QPushButton[summaryQueue]:hover {{ background: {COLOR_BRAND_SOFT}; border-color: {COLOR_BORDER_STRONG}; }}
QPushButton[summaryQueue="pending"] {{ border-right: 4px solid {COLOR_ACCENT_ORANGE}; }}
QPushButton[summaryQueue="unassigned"] {{ border-right: 4px solid {COLOR_ACCENT_SKY}; }}
QPushButton[summaryQueue="approved"] {{ border-right: 4px solid {COLOR_ACCENT_LEAF}; }}
QLabel#activityImagePreview {{ background: #F8FBFB; border: 1px solid #E4ECEB; border-radius: {RADIUS_MEDIUM}px; color: {COLOR_TEXT_MUTED}; }}
QToolButton#managementRowOpenAction {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: {SPACE_1}px; }}
QToolButton#managementRowOpenAction:hover {{ background: {COLOR_SELECTED}; border-color: {COLOR_FOCUS}; }}
QToolButton#managementRowOpenAction[managementReferenceRowAction="true"] {{ background: transparent; border: none; color: {COLOR_TEXT_MUTED}; font-size: 20px; font-weight: {FONT_WEIGHT_TITLE}; padding: 0; }}
QToolButton#managementRowOpenAction[managementReferenceRowAction="true"]:hover {{ background: {COLOR_BRAND_SOFT}; border: none; color: {COLOR_BRAND}; }}
QToolButton#managementRowOpenAction:pressed {{ background: {COLOR_SURFACE_ALT}; }}
QToolButton#managementRowOpenAction[customerRowAction="true"] {{ background: transparent; border: none; color: {COLOR_TEXT_MUTED}; font-size: 20px; font-weight: {FONT_WEIGHT_TITLE}; padding: 0; }}
QToolButton#managementRowOpenAction[customerRowAction="true"]:hover {{ background: {COLOR_BRAND_SOFT}; border: none; color: {COLOR_BRAND}; }}
QToolButton#managementRowOpenAction[customerRowAction="true"]:pressed {{ background: {COLOR_SELECTED}; border: none; }}
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
QTableWidget[customerTable="true"] {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MEDIUM}px; }}
QTableWidget[customerTable="true"] QHeaderView::section {{ background: #F2F9F8; color: {COLOR_BRAND}; }}
QFrame[aiMessage="user"] {{ background: {COLOR_AI_USER_BACKGROUND}; border: 1px solid #C9E9ED; border-radius: {RADIUS_MEDIUM}px; }}
QFrame[aiMessage="assistant"] {{ background: {COLOR_AI_ASSISTANT_BACKGROUND}; border: 1px solid #F1D8AA; border-radius: {RADIUS_MEDIUM}px; }}
QFrame[aiSource="true"] {{ background: {COLOR_AI_SOURCE_BACKGROUND}; border: 1px solid #D8E8C9; border-radius: {RADIUS_SMALL}px; }}
QFrame[referenceCard="true"] {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_LARGE}px; }}
QFrame[referenceCard="true"] QLabel#sectionTitle {{ color: {COLOR_BRAND}; font-size: 20px; font-weight: {FONT_WEIGHT_TITLE}; background: transparent; }}
QLabel[referenceFieldLabel="true"] {{ color: {COLOR_TEXT}; font-weight: {FONT_WEIGHT_LABEL}; background: transparent; }}
QFrame[referenceCard="true"] QLineEdit, QFrame[referenceCard="true"] QTextEdit, QFrame[referenceCard="true"] QComboBox {{
    min-height: {CONTROL_HEIGHT_COMPACT}px; background: {COLOR_SURFACE}; color: {COLOR_TEXT}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SMALL}px; padding: 0 {SPACE_2}px;
    selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED};
}}
QFrame[referenceCard="true"] QTextEdit {{ padding: {SPACE_2}px; }}
QFrame[referenceCard="true"] QLineEdit:focus, QFrame[referenceCard="true"] QTextEdit:focus, QFrame[referenceCard="true"] QComboBox:focus {{ border: 2px solid {COLOR_FOCUS}; color: {COLOR_TEXT}; }}
QLineEdit, QTextEdit, QPlainTextEdit {{ selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; }}
QComboBox QLineEdit {{ color: {COLOR_TEXT}; selection-color: {COLOR_TEXT}; selection-background-color: {COLOR_SELECTED}; }}
QFrame[managementDetailCard="true"] {{ min-height: 110px; }}

/* Approved login composition. */
QFrame#loginPanel {{
    background: rgba(255, 255, 255, 246);
    border: 1px solid #D6E0E3;
    border-radius: 14px;
}}
QLabel#loginWelcomeTitle {{ font-size: 27px; font-weight: {FONT_WEIGHT_TITLE}; color: {COLOR_TEXT}; background: transparent; }}
QLabel#loginBrandSubtitle {{ font-size: 18px; color: {COLOR_TEXT}; background: transparent; }}
QLabel#loginDescription {{ color: {COLOR_TEXT_MUTED}; font-size: 15px; background: transparent; }}
QLabel#loginFieldLabel {{ color: {COLOR_TEXT}; font-weight: {FONT_WEIGHT_LABEL}; background: transparent; }}
QLabel#loginForgotPassword {{ color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_SUPPORTING}px; background: transparent; }}
QFrame#loginPanel QLineEdit {{
    min-height: {CONTROL_HEIGHT_LARGE}px;
    background: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid #CBD7DD;
    border-radius: 6px;
    padding: 0 {SPACE_3}px;
    selection-color: {COLOR_TEXT};
    selection-background-color: {COLOR_SELECTED};
}}
QFrame#loginPanel QLineEdit:focus {{ border: 2px solid {COLOR_FOCUS}; color: {COLOR_TEXT}; }}

/* Approved AI chat composition. */
QWidget#aiChatPage {{ background: {COLOR_BACKGROUND}; }}
QFrame#aiConversationCard {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_LARGE}px; }}
QScrollArea#aiConversationScroll, QScrollArea#aiConversationScroll > QWidget > QWidget, QWidget#aiMessagesHost {{ background: transparent; border: none; }}
QFrame[aiMessage="user"] {{ background: #EFF8FD; border: 1px solid #C9E3F2; border-radius: 12px; }}
QFrame[aiMessage="assistant"] {{ background: #FBFDF7; border: 1px solid #D9E7C8; border-radius: 12px; }}
QLabel#aiMessageSender {{ color: {COLOR_TEXT}; font-weight: {FONT_WEIGHT_LABEL}; background: transparent; }}
QLabel#aiMessageBody {{ color: {COLOR_TEXT}; background: transparent; line-height: 1.35; }}
QLabel#aiAvatarUser {{ color: {COLOR_BRAND}; background: #EEF8FC; border: 1px solid #CBE7F1; border-radius: 20px; font-size: 20px; }}
QLabel#aiAvatarAssistant {{ background: transparent; border: none; }}
QFrame[aiSource="true"] {{ background: #F8FBF1; border: 1px solid #CFDDBD; border-radius: 8px; }}
QLabel#aiSourceTitle {{ color: {COLOR_TEXT}; font-weight: {FONT_WEIGHT_LABEL}; background: transparent; }}
QFrame#aiComposerCard {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: 12px; }}
QLineEdit#aiPromptInput {{
    min-height: 44px;
    background: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: none;
    padding: 0 {SPACE_3}px;
    selection-color: {COLOR_TEXT};
    selection-background-color: {COLOR_SELECTED};
}}
QLineEdit#aiPromptInput:focus {{ border: none; color: {COLOR_TEXT}; }}
QLabel#aiStateLabel {{ color: {COLOR_TEXT_MUTED}; background: transparent; padding: 0 {SPACE_2}px; }}
QScrollArea#knowledgeContentScroll,
QScrollArea#knowledgeContentScroll > QWidget > QWidget {{ background: transparent; border: none; }}
"""


def build_neutral_stylesheet() -> str:
    """Backward-compatible name for the now-branded global stylesheet."""
    return build_branded_stylesheet()