import regex

from enum import auto, IntFlag
from typing import Any, Iterable, NamedTuple, TYPE_CHECKING

from discord_app import (
  QEvent, Qt, QObject, QPropertyAnimation, pyqtProperty, QFile,
  QParallelAnimationGroup, QEasingCurve, QColor, QSvgWidget, QWidget, QLayout,
  QAbstractButton, QLabel, QGraphicsColorizeEffect, QGraphicsOpacityEffect,
  QBrush, QPainter, QPainterPath,
  ChannelDropdown, TooltipSummons, qsignals
)

SUPPRESSION = regex.compile(r'/\*\s*suppress\s*(.*?)\*/')
COMMENTS = regex.compile(r'/\*.*?\*/')
ENTRIES = regex.compile(r'\s*(.*?)\s*\{\s*(.*?)\s*\}')
ELEMENTS = regex.compile(r'\s*(.*?)\s*:\s*(.*?);\s*')

INHERITED_KEYS = set([
  'font',
  'font-family',
  'font-size',
  'font-style',
  'font-weight',
  'color'
])

################################################################################

class State(IntFlag):
  HOVER = auto()
  UNHOVER = auto()
  TOGGLE_HOVER = HOVER | UNHOVER

  CHECKED = auto()
  UNCHECKED = auto()
  TOGGLE_CHECKED = CHECKED | UNCHECKED

  DRAGGED = auto()
  UNDRAGGED = auto()
  TOGGLE_DRAGGED = DRAGGED | UNDRAGGED

  DRAGHOVER = auto()
  UNDRAGHOVER = auto()
  TOGGLE_DRAGHOVER = DRAGHOVER | UNDRAGHOVER

  NOTIFY = auto()
  UNNOTIFY = auto()
  TOGGLE_NOTIFY = NOTIFY | UNNOTIFY

  ACTIVE = auto()
  UNACTIVE = auto()
  TOGGLE_ACTIVE = ACTIVE | UNACTIVE

  DEFAULT = UNHOVER | UNCHECKED | UNDRAGGED | UNNOTIFY | UNACTIVE
  MAX_VALUE = auto()

class Selector(NamedTuple):
  qualname: str
  state: State
  has: 'list[Selector] | None'
  is_direct_descendant: bool

  @classmethod
  def parse_list(cls, source: str) -> 'list[Selector]':
    selectors: list[Selector] = []
    tokens = iter(source.replace('>', ' > ').split())
    while token := next(tokens, None):
      direct = token == '>' and bool(token := next(tokens, None))
      selectors.append(Selector.parse(token, direct))
    return selectors

  @classmethod
  def parse(cls, source: str, direct: bool) -> 'Selector':
    selector, has = regex.match(r'(.*?)(?::has\((.*)\))?$', source).groups()
    tokens = selector.split(':')
    state = State(0)
    for pseudo_class in tokens[1:]:
      state |= State[pseudo_class.upper()]
    if has is not None: has = Selector.parse_list(has)
    return Selector(tokens[0], state, has, direct)

class StylesheetEntry(NamedTuple):
  selectors: list[Selector]
  elements: dict[str, str]

by_qualname: dict[str, list[StylesheetEntry]] = {}
with open(QFile('root:stylesheet.css').fileName()) as file:
  stylesheet = SUPPRESSION.sub(r'\1', file.read().replace('\n', ''))
  stylesheet = COMMENTS.sub('', stylesheet)
for match_ in ENTRIES.finditer(stylesheet):
  selectors, elements = match_.groups()
  elements = dict(map(regex.Match.groups, ELEMENTS.finditer(elements)))
  for source in selectors.split(','):
    selectors = Selector.parse_list(source)
    entry = StylesheetEntry(selectors, elements)
    by_qualname.setdefault(selectors[-1].qualname, []).append(entry)

class StyleCondtion(NamedTuple):
  target: QWidget
  state: State

class StyleSource(NamedTuple):
  conditions: list[StyleCondtion]
  value: str

class AbstractProperty(QObject):
  
  NAME = b'value'
  if TYPE_CHECKING:
    value: ...
    def __init__(self, parent: QWidget, initial: ...) -> None: ...
  
  @classmethod
  def implement_for(cls, type: type) -> 'type[AbstractProperty]':
    class Implements(cls):

      @pyqtProperty(type)
      def value(self) -> type: return self.actual
      @value.setter
      def value(self, value: type) -> None: self.actual = value

      def __init__(self, parent: QWidget, initial: type | None) -> None:
        super().__init__(parent)
        self.actual = initial or type()
    return Implements
  
  def __str__(self) -> str:
    match src := self.value:
      case QColor():
        r, g, b, a = src.red(), src.green(), src.blue(), src.alpha()
        if a == 255: return f'rgb({r}, {g}, {b})'
        else: return f'rgba({r}, {g}, {b}, {a / 255.})'
      case int():
        return f'{src}px'
      case float():
        return str(src)
      case _: raise ValueError(f'unsupported type {type(src)}')
  
ColorProperty = AbstractProperty.implement_for(QColor)
FloatProperty = AbstractProperty.implement_for(float)
IntProperty = AbstractProperty.implement_for(int)

# TODO distance to px and time to ms
def atoi(src: str) -> int:
  return int(''.join(filter('-1234567890'.__contains__, src)))

def atot(src: str) -> QColor | int | float: # TODO add to AbstractProperty?
  if src.startswith('rgb('):
    return QColor(*eval(src[3:]))
  elif src.startswith('rgba('):
    r, g, b, a = eval(src[4:])
    return QColor(r, g, b, int(a * 255))
  elif regex.match(r'[0-9]+[px|pt|em|ex]', src):
    return int(src[:-2])
  elif regex.match(r'[-0-9\.]*', src):
    return float(src)
  else:
    raise ValueError(f'unsupported string {src}')

class EventFilter(QObject):

  def eventFilter(self, target: QWidget, event: QEvent) -> bool:
    if event.type() is event.Type.Enter:
      target.__style__.toggle_hover(True)
      if target.__style__.state & State.DRAGHOVER:
        target.__style__.toggle_draghover(False)
    elif event.type() is event.Type.Leave:
      target.__style__.toggle_hover(False)
    elif event.type() is event.Type.DragEnter:
      target.__style__.toggle_draghover(True)
    elif event.type() is event.Type.DragLeave:
      target.__style__.toggle_draghover(False)
    return super().eventFilter(target, event)

class WidgetStyle:

  EVENT_FILTER = EventFilter()

  def __init__(self, target: QWidget, layout: type[QLayout] | None) -> None:
    self.target = target
    self.state = State.DEFAULT
    self.callbacks: set[QWidget] = set()
    self.transitions: \
      dict[str, tuple[AbstractProperty, QPropertyAnimation]] = {}
    if layout: layout(target)

    if (parent := target.parentWidget()) and hasattr(parent, '__style__'):
      self.elements = {
        k: v.copy()
          for k, v in parent.__style__.elements.items() if k in INHERITED_KEYS
      }
    else:
      self.elements: dict[str, list[StyleSource]] = {}

    pwo = [target]
    while parent:
      pwo.append(parent)
      parent = parent.parentWidget()

    self.push_applicable('*', pwo)
    self.push_applicable(target.__class__.__qualname__, pwo)
    self.push_applicable('#' + target.objectName(), pwo)

    # TODO check elements

    if 'background' in self.elements:
      self.target.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    if sbw := self.elements.pop('scrollbar-width', None):
      if len(sbw) > 1 or any(c.state for c in sbw[0].conditions):
        raise ValueError(f'conditions for scrollbar-width ({self.target})')
      setattr(self, 'scrollbar-width', atoi(sbw[0].value))
    
    if t_sources := self.elements.pop('transition', None):
      # TODO support multiple transition entries for unique properties
      if len(t_sources) > 1 or any(c.state for c in t_sources[0].conditions):
        raise ValueError(f'conditions for transition ({self.target})')
      self.animations = QParallelAnimationGroup(self.target)
      for transition in t_sources[0].value.split(','):
        key, duration, timing = transition.split()
        match key:
          case 'background':    p_type = ColorProperty
          case 'color':         p_type = ColorProperty
          case 'rotate':        p_type = FloatProperty
          case 'border-radius': p_type = IntProperty
          case 'margin-top':    p_type = IntProperty
          case 'margin-bottom': p_type = IntProperty
          case _: raise ValueError(f'unsupported property {key}')
        match timing:
          case 'linear':      curve = QEasingCurve.Type.Linear
          case 'ease-out':    curve = QEasingCurve.Type.OutQuad # TODO actual
          case 'ease-in-out': curve = QEasingCurve.Type.InOutQuad
          case _: raise ValueError(f'unsupported bezier {timing}')
        sources = self.elements.get(key)
        for source in sources:
          if not any(c.state for c in source.conditions):
            initial = atot(source.value)
            break
        else: initial = None
        setattr(self, f'_p_{key}', prop := p_type(self.target, initial))
        animation = QPropertyAnimation(prop, p_type.NAME, prop)
        animation.setEndValue(prop.value)
        animation.setDuration(atoi(duration))
        animation.setEasingCurve(curve)
        self.transitions[key] = (prop, animation)
        self.animations.addAnimation(animation)
        animation.valueChanged.connect(self.set_style)

    if c_sources := self.elements.pop('cursor', None):
      # TODO more support for cursor override
      if any(c.state for c in c_sources[0].conditions):
        raise ValueError(f'conditions for cursor ({self.target})')
      match cursor := c_sources[0].value:
        case 'pointer': shape = Qt.CursorShape.PointingHandCursor
        case _: raise ValueError(f'unsupported cursor {cursor}')
      target.setCursor(shape)

    target.installEventFilter(self.EVENT_FILTER)
    if isinstance(target, QAbstractButton):
      target.toggled.connect(self.toggle_checked)
    if hasattr(target, 'dragged'):
      target.dragged.connect(self.toggle_dragged)
    if hasattr(target, 'notify'):
      target.notify.connect(self.toggle_notify)
    if hasattr(target, 'active'):
      target.active.connect(self.toggle_active)

  def toggle_hover(self, hover: bool) -> None:
    if not self.state & (State.UNHOVER << hover):
      self.state ^= State.TOGGLE_HOVER
      self.perform_callbacks()
  
  def toggle_checked(self, checked: bool) -> None:
    if not self.state & (State.UNCHECKED << checked):
      self.state ^= State.TOGGLE_CHECKED
      self.perform_callbacks()
  
  def toggle_dragged(self, dragged: bool) -> None:
    if not self.state & (State.UNDRAGGED << dragged):
      self.state ^= State.TOGGLE_DRAGGED
      self.perform_callbacks()

  def toggle_draghover(self, draghover: bool) -> None:
    if not self.state & (State.UNDRAGHOVER << draghover):
      self.state ^= State.TOGGLE_DRAGHOVER
      self.perform_callbacks()
  
  def toggle_notify(self, notify: bool) -> None:
    if not self.state & (State.UNNOTIFY << notify):
      self.state ^= State.TOGGLE_NOTIFY
      self.perform_callbacks()

  def toggle_active(self, active: bool) -> None:
    if not self.state & (State.UNACTIVE << active):
      self.state ^= State.TOGGLE_ACTIVE
      self.perform_callbacks()
  
  def push_applicable(self, qualname: str, pwo: list[QWidget]) -> None:
    for entry in by_qualname.get(qualname, []):
      selectors = iter(reversed(entry.selectors))
      lineage = iter(pwo)
      direct = False
      conditions: list[StyleCondtion] = []

      # TODO SPAGHETTI
      while selector := next(selectors, None):
        sentinel = True
        while sentinel and (widget := next(lineage, None)):

          self_match = selector.qualname == '*' \
            or selector.qualname == widget.__class__.__qualname__ \
            or selector.qualname == '#' + widget.objectName()
          if self_match and selector.has:
            if len(selector.has) > 1:
              raise ValueError(f':has cannot contain list')
            h_selector = selector.has[0]
            for h_widget in widget.findChildren(QWidget, '',
              Qt.FindChildOption.FindDirectChildrenOnly
                if h_selector.is_direct_descendant else
              Qt.FindChildOption.FindChildrenRecursively
            ) or []: # TODO binds to first child found only
              if h_widget.__class__.__qualname__ == h_selector.qualname:
                has_match = True
                break
            else: has_match = False
          
          if self_match and (not selector.has or has_match):
            if selector.state:
              conditions.append(StyleCondtion(widget, selector.state))
            if selector.has and h_selector.state:
              conditions.append(StyleCondtion(h_widget, h_selector.state))
            break
          elif direct: sentinel = False

        else: break
        direct = selector.is_direct_descendant
      else:
        for k, v in entry.elements.items():
          for k, v in self.expand_compound_styles(k, v):
            sources = self.elements.setdefault(k, [])
            sources.insert(0, StyleSource(conditions, v))

  @classmethod
  def expand_compound_styles(cls, key: str, value: str):
    if key == 'height' or key == 'width':
      yield f'min-{key}', value
      yield f'max-{key}', value
    elif key == 'margin' or key == 'padding':
      args = value.split()
      yield f'{key}-top', (top := args[0])
      yield f'{key}-right', (right := args[1] if len(args) > 1 else top)
      yield f'{key}-bottom', args[2] if len(args) > 2 else top
      yield f'{key}-left', args[3] if len(args) > 3 else right
    # TODO not supported because not compatible with animation
    # elif key == 'border-radius':
    #   for side in ['top-left', 'top-right', 'bottom-right', 'bottom-left']:
    #     yield f'border-{side}-radius', value
    elif key == 'tooltip' and \
      (not value.startswith('"') or not value.endswith('"')):
      yield key, f'"{value}"'
    else:
      yield key, value
  
  def handle_custom_styles(self, style: dict[str, str]) -> None:
    layout = self.target.layout()

    if opacity := style.pop('opacity', None):
      effect = self.target.graphicsEffect()
      if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(self.target)
        self.target.setGraphicsEffect(effect)
      effect.setOpacity(atot(opacity))
    elif isinstance(self.target.graphicsEffect(), QGraphicsOpacityEffect):
      self.target.setGraphicsEffect(None)

    if isinstance(self.target, QSvgWidget):
      if color := style.pop('color', None):
        effect = self.target.graphicsEffect()
        if not isinstance(effect, QGraphicsColorizeEffect):
          effect = QGraphicsColorizeEffect(self.target)
          self.target.setGraphicsEffect(effect)
        effect.setColor(atot(color))

    if min_width := style.pop('min-width', None):
      self.target.setMinimumWidth(atoi(min_width))
    if max_width := style.pop('max-width', None):
      self.target.setMaximumWidth(atoi(max_width))
    if min_height := style.pop('min-height', None):
      self.target.setMinimumHeight(atoi(min_height))
    if max_height := style.pop('max-height', None):
      self.target.setMaximumHeight(atoi(max_height))
    
    target = self.target if layout is None else layout
    margins, padding = [0, 0, 0, 0], [0, 0, 0, 0]
    for i, side in enumerate(['left', 'top', 'right', 'bottom']):
      margins[i] += atoi(style.get(f'margin-{side}', '0px'))
      padding[i] += atoi(style.get(f'padding-{side}', '0px'))
    target.setContentsMargins(*map(int.__add__, margins, padding))
    if isinstance(self.target, QLabel) and not any(margins):
      style['padding'] = '0px' # TODO why? magic

    left, top = style.pop('left', None), style.pop('top', None)
    if left or top:
      self.target.move(atoi(left) if left else 0, atoi(top) if top else 0)

    if (spacing := style.pop('spacing', None)) and layout is not None:
      layout.setSpacing(atoi(spacing))

    anchor = style.pop('tooltip-anchor', 'top')
    distance = atoi(style.pop('tooltip-distance', '0px'))
    text = style.pop('tooltip', None)
    summons = TooltipSummons(self.target, anchor, text, distance)
    qsignals.tooltip_summons.emit(summons if text else None)

    if isinstance(self.target, ChannelDropdown) and \
      (angle := style.pop('rotate', None)):
      self.target.rotate(angle)

  def style_generator(self):
    for k, sources in self.elements.items():
      for source in sources:
        if source.conditions is None:
          yield k, source.value
          break
        for condition in source.conditions:
          target = condition.target.__style__ \
            if condition.target is not self.target else self
          if condition.state & target.state != condition.state:
            break
        else:
          yield k, source.value
          break
  
  def animation_filter(self, style: Iterable[tuple[str, str]]):
    animated = False
    for k, v in style:
      if k in self.transitions:
        property, animation = self.transitions[k]
        if animation.endValue() != (end_value := atot(v)):
          animation.setEndValue(end_value)
          animated = True
        yield k, str(property)
      else:
        yield k, v
    if animated:
      self.animations.stop()
      self.animations.start()
  
  def set_style(self, *, exclude: list[str]=[]) -> None:
    style = dict(self.animation_filter(self.style_generator()))
    for key in exclude: style.pop(key, None)
    self.handle_custom_styles(style)
    self.last_style = style
    if style: self.target.setStyleSheet(
      self.target.__class__.__qualname__.split('.')[-1] + \
      ' { ' + '; '.join(
        f'{k}: {v}' for k, v in style.items()
      ) + '; }'
    )
      
  def register_callbacks(self) -> None:
    for sources in self.elements.values():
      for source in sources:
        for condition in source.conditions:
          if condition.state:
            condition.target.__style__.callbacks.add(self.target)

  def perform_callbacks(self) -> None:
    if self.callbacks:
      for widget in self.callbacks:
        widget.__style__.set_style()
  
  def set(self, key: str, value: Any, state: State=State(0)) -> None:
    if value:
      for k, v in self.expand_compound_styles(key, value):
        source = StyleSource([StyleCondtion(self.target, state)], v)
        self.elements.setdefault(k, []).insert(0, source)
      if state: self.register_callbacks()
    else: self.elements.pop(key, None)
    self.set_style()

constructor = QWidget.__init__
def __init__(self: QWidget, *args, **kwargs) -> None:
  layout = kwargs.pop('layout', None)
  name = kwargs.pop('name', None)
  exclude = kwargs.pop('exclude', [])
  constructor(self, *args, **kwargs)
  if name: self.setObjectName(name)
  self.__style__ = WidgetStyle(self, layout)
  self.__style__.set_style(exclude=exclude)
  self.__style__.register_callbacks()
QWidget.__init__ = __init__

get_style = QWidget.style
def style(self: QWidget, *args, **kwargs):
  if not args and not kwargs:
    return get_style(self)
  else:
    self.__style__.set(*args, **kwargs)
QWidget.style = style

class RoundedIconMixin:

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.brush = QBrush(Qt.GlobalColor.transparent)
  
  def paintEvent(self, _) -> None:
    super().paintEvent(_)
    radius = atoi(self.__style__.last_style.get('border-radius', '0px'))
    path = QPainterPath()
    path.addRoundedRect(self.contentsRect().toRectF(), radius, radius)
    painter = QPainter(self)
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)
    painter.fillPath(path, self.brush)

__all__ = ['State', 'atoi', 'RoundedIconMixin']

################################ Implemented ################################

# ** height: Length
#   min-height: Length (must be set manually)
#   max-height: Length (must be set manually)
# ** width: Length
#   min-width: Length (must be set manually)
#   max-width: Length (must be set manually)

# ** margin: Box Lengths
#   margin-top: Length
#   margin-right: Length
#   margin-bottom: Length
#   margin-left: Length

# ** padding: Box Lengths
#   padding-top: Length
#   padding-right: Length
#   padding-bottom: Length
#   padding-left: Length

################################ Used ################################

# text-align: Alignment

# border-radius: Radius
#   border-top-left-radius
#   border-top-right-radius
#   border-bottom-right-radius
#   border-bottom-left-radius

# background: Background
#   background-color: Brush
#   background-image: Url
#   background-repeat: Repeat = repeat
#   background-position: Alignment = top left
# background-clip: Origin = border
# background-origin: Origin  = padding

# color: Brush
# placeholder-text-color: Brush

# ** opacity: Number (does not apply to widgets)

# font: Font
#   font-family: String
#   font-size: Font Size
#   font-style: Font Style
#   font-weight: Font Weight
# text-decoration: none | underline | overline | line-through

# ** spacing: Length (does not apply to layouts)

# icon: Url+ (QPushButton only)
# icon-size: Length

# widget-animation-duration: Number

################################ Maybe Used ################################

# messagebox-text-interaction-flags: Number

# outline
#   outline-color
#   outline-offset
#   outline-style
#   outline-radius
#     outline-bottom-left-radius
#     outline-bottom-right-radius
#     outline-top-left-radius
#     outline-top-right-radius

################################ Unused ################################

# alternate-background-color: Brush = palette.AlternateBase
#   (QAbstractItemView subclasses)
# background-attachment: Attachment = scroll
#   (QAbstractScrollArea background-image)

# image: Url+
#   (subcontrols not used)
# image-position: Alignment+
#   (subcontrols not used)

# border-image: Border Image
#   (border images not used)
# border: Border
#   border-color: Box Colors
#   border-style: Border Style
#   border-width: Box Lengths
#   border-top
#     border-top-color
#     border-top-style
#     border-top-width
#   border-right
#     border-right-color
#     border-right-style
#     border-right-width
#   border-bottom
#     border-bottom-color
#     border-bottom-style
#     border-bottom-width
#   border-left
#     border-left-color
#     border-left-style
#     border-left-width

# bottom: Length
#   (subcontrols not used)
# left: Length
#   (subcontrols not used)
# right: Length
#   (subcontrols not used)
# top: Length
# position: relative | absolute
#   (subcontrols not used)
# subcontrol-origin: Origin
#   (subcontrols not used)
# subcontrol-position: Alignment
#   (subcontrols not used)

# button-layout: Number
#   (QDialogBox or QMessageBox button layouts not used)

# dialogbuttonbox-buttons-have-icons: Boolean
#   (QDialogButtonBox not used)

# gridline-color: Color
#   (QTableView not used)

# lineedit-password-character: Number
#   (QLineEdit passwords not used)
# lineedit-password-mask-delay: Number
#   (QLineEdit passwords not used)

# paint-alternating-row-colors-for-empty-area
#   (QTreeView not used)

# selection-background-color: Brush
#   (selection text not used)
# selection-color: Brush
#   (selection text not used)

# show-decoration-selected: Boolean
#   (QListView not used)

# titlebar-show-tooltips-on-buttons
#   (QToolTip not used)
