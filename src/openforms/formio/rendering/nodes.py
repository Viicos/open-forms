import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterator, Literal, Optional, Union

from glom import Path, assign, glom

from openforms.submissions.models import SubmissionStep
from openforms.submissions.rendering.base import Node
from openforms.submissions.rendering.constants import RenderModes

from ..service import format_value, translate_function
from ..typing import Component
from ..utils import (
    is_layout_component,
    is_visible_in_frontend,
    iterate_components_with_configuration_path,
)

if TYPE_CHECKING:
    from openforms.submissions.rendering import Renderer


@dataclass
class RenderConfiguration:
    """
    Component-level property configuration to control output.

    Whether a component should be emitted or not is/can be configured on the component
    in the form designer. In the event that this key is missing from the component (
    because it is not supported or is a form definition from before this feature
    landed), then fall back using the ``default``.
    """

    key: Optional[str]
    default: bool


@dataclass
class ComponentNode(Node):
    component: Component
    step: SubmissionStep
    depth: int = 0
    is_layout = False
    path: Path = None  # Path in the data (#TODO rename to data_path?)
    json_renderer_path: Path = None  # Special data path used by the JSON rendering in openforms/formio/rendering/nodes.py #TODO Refactor?
    configuration_path: str = None  # Path in the configuration tree, matching the path obtained with openforms/formio/utils.py `flatten_by_path`
    parent_node: Node = None

    @staticmethod
    def build_node(
        step: SubmissionStep,
        component: Component,
        renderer: "Renderer",
        path: Path | None = None,  # Path in the data
        json_renderer_path: Path | None = None,
        configuration_path: str | None = None,
        depth: int = 0,
        parent_node: Node | None = None,
    ) -> "ComponentNode":
        """
        Instantiate the most specific node type for a given component type.
        """
        from .registry import register

        node_cls = register[component["type"]]
        nested_node = node_cls(
            step=step,
            component=component,
            renderer=renderer,
            depth=depth,
            path=path,
            json_renderer_path=json_renderer_path,
            configuration_path=configuration_path,
            parent_node=parent_node,
        )
        return nested_node

    def __post_init__(self):
        # Value Formatters have no access to the translations; run all our
        # labels through the translations, before further processing of logic
        # etc.
        if self.renderer.form.translation_enabled and self.step.form_step:
            self.apply_to_labels(
                translate_function(self.renderer.submission, self.step)
            )

    @property
    def is_visible(self) -> bool:
        """
        Implement the logic to determine if a component is visible.

        See https://github.com/open-formulieren/open-forms/issues/1451#issuecomment-1077506877
        for a diagram of the logic powering this.

        Summarized, a component is visible for a given render mode if the component-level
        configuration says so (while falling back to some defaults for older configurations).

        The exceptions to this are:

        - fieldsets are visible if:

          - any of the children is visible (no render_mode dependency)
          - not `hidden` (no render_mode dependency)
          - (not `hideHeader`) -> render children, but not the label

        - fieldsets:

          - never render the label

        - wysiwyg:

          - in PDF and summary if visible

        These exceptions are handled in more specific subclasses to avoid massive if-else
        branches again, see :mod:`openforms.formio.rendering.default`.
        """
        from .conf import RENDER_CONFIGURATION  # circular import
        from .default import EditGridGroupNode

        # everything is emitted in export mode to get consistent columns
        if self.mode == RenderModes.export:
            return True

        # explicitly hidden components never show up. Note that this property can be set
        # by logic rules or by frontend logic!
        # We only pass the step data, since frontend logic only has access to the current step data.
        if isinstance(self.parent_node, EditGridGroupNode):
            # Frontend logic for repeating group does not specify the index of the iteration. So we need to look at
            # the data for a specific iteration to figure out if a field within the iteration is visible
            step_data = copy.deepcopy(self.step.data)
            current_iteration_data = glom(step_data, self.path, default=None)
            artificial_repeating_group_data = assign(
                step_data, self.parent_node.path, current_iteration_data, missing=dict
            )
            if not is_visible_in_frontend(
                self.component, artificial_repeating_group_data
            ):
                return False
        elif not is_visible_in_frontend(self.component, self.step.data):
            return False

        render_configuration = RENDER_CONFIGURATION[self.mode]
        # it's possible the end-user cannot explicitly configure the visibility, in
        # which case the system default is used.
        if render_configuration.key is None:
            return render_configuration.default

        # if there is a property key, try to read it but fall back to the system default
        # if it's absent.
        should_render = self.component.get(
            render_configuration.key, render_configuration.default
        )
        return should_render

    @property
    def value(self) -> Any:
        """
        Obtain the value from the submission for this component.

        Note that this returns an unformatted value. There also has not been done
        any Formio type -> Python type casting, so a datetime will be an ISO-8601
        datestring for example.

        TODO: build and use the type conversion for Formio components.
        """
        path = Path(self.path, self.key_as_path) if self.path else self.key_as_path

        value = glom(self.step.data, path, default=None)
        return value

    @property
    def prefix(self) -> str:
        return self.configuration_path or "components"

    def get_children(self) -> Iterator["ComponentNode"]:
        """
        Yield the child components if this component is a container type.
        """
        for configuration_path, component in iterate_components_with_configuration_path(
            configuration=self.component,
            prefix=self.prefix,
            recursive=False,
        ):
            yield ComponentNode.build_node(
                step=self.step,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
                path=self.path,
                json_renderer_path=Path(self.json_renderer_path, self.key_as_path)
                if self.json_renderer_path
                else Path(self.key_as_path),
                configuration_path=configuration_path,
            )

    def __iter__(self) -> Iterator["ComponentNode"]:
        """
        Yield depth-first children, including itself.
        """
        if not self.is_visible:
            return

        # in export mode, only emit if the component is not a layout component
        if self.mode != RenderModes.export or not is_layout_component(self.component):
            yield self

        for child in self.get_children():
            if not child.is_visible:
                continue
            yield from child

    @property
    def spans_full_width(self) -> bool:
        """
        Whether the display value spans the full width rather than 2 columns.
        """
        return False

    @property
    def layout_modifier(self) -> str:
        """
        For HTML based rendering, potentially emit a layout modifier.
        """
        return "root" if self.component.get("_is_root", False) else ""

    @property
    def label(self) -> str:
        """
        Obtain the (human-readable) label for the Formio component.
        """
        if self.mode == RenderModes.export:
            return self.component.get("key") or "KEY_MISSING"
        return self.component.get("label") or self.component.get("key", "")

    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        """
        Apply a function f to all labels.
        """
        if "label" in self.component:
            self.component["label"] = f(self.component["label"])

    @property
    def display_value(self) -> Union[str, Any]:
        """
        Format the value according to the render mode and/or output content type.

        This applies the registry of Formio formatters to the value based on the
        component type, using :func:`openforms.formio.service.format_value`.
        """
        # in export mode, expose the raw datatype
        if self.mode == RenderModes.export:
            return self.value
        return format_value(self.component, self.value, as_html=self.renderer.as_html)

    @property
    def indent(self) -> str:
        return "    " * self.depth if not self.as_html else ""

    def render(self) -> str:
        """
        Output a simple key-value pair of label and value.
        """
        return f"{self.indent}{self.label}: {self.display_value}"

    @property
    def key(self):
        return self.component["key"]

    @property
    def key_as_path(self) -> Path:
        """
        See https://glom.readthedocs.io/en/latest/api.html?highlight=Path#glom.Path
        Using Path("a.b") in glom will not use the nested path, but will look for a key "a.b"
        """
        return Path.from_text(self.key)


@dataclass
class FormioNode(Node):
    step: SubmissionStep

    def render(self) -> Literal[""]:
        return ""

    def get_children(self) -> Iterator[ComponentNode]:
        configuration = self.step.form_step.form_definition.configuration
        for configuration_path, component in iterate_components_with_configuration_path(
            configuration, recursive=False
        ):
            child_node = ComponentNode.build_node(
                step=self.step,
                component=component,
                renderer=self.renderer,
                configuration_path=configuration_path,
            )
            yield from child_node
