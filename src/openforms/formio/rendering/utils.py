from typing import TYPE_CHECKING

from glom import Assign, Path, glom

from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.rendering.nodes import SubmissionStepNode
from openforms.typing import JSONObject

from .default import ColumnsNode, EditGridGroupNode, EditGridNode, FieldSetNode
from .nodes import ComponentNode

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


def render_nested_json(submission: "Submission") -> JSONObject:
    """Render submission as JSON with nesting

    The data is nested within each submission step (using the form definition slug as key).
    The data is nested for fieldset components and for column components.
    """
    renderer = Renderer(
        submission=submission, mode=RenderModes.registration, as_html=False
    )

    data = {}
    current_step_slug = None
    for node in renderer:
        if isinstance(node, SubmissionStepNode):
            current_step_slug = node.step.form_step.form_definition.slug
            data[current_step_slug] = {}
            continue

        if isinstance(node, EditGridGroupNode):
            node_path = Path(current_step_slug, node.configuration_path)
            editgrid_array = glom(data, node_path)
            editgrid_array.append({})
            continue

        if isinstance(node, ComponentNode):
            node_path = (
                Path(current_step_slug, node.configuration_path, node.key)
                if node.configuration_path
                else Path(current_step_slug, node.key)
            )

            value = {} if isinstance(node, (FieldSetNode, ColumnsNode)) else node.value
            if isinstance(node, EditGridNode):
                value = []

            glom(data, Assign(node_path, value, missing=dict))

    return data
