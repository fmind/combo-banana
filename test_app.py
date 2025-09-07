"""Tests of the app."""

# %% IMPORTS

import gradio as gr
import pytest
from PIL import Image

import app

# %% TESTS


def test_define():
    """Tests the define function."""
    # given
    input = "Add a step to convert the image to black and white"
    workflow = app.Workflow(
        name="Remove background",
        steps=[
            app.Step(title="Remove Background", prompt="Remove the background from the image."),
        ],
    )
    # when
    new_input, output, workflow = app.define(input=input, workflow=workflow)
    # then
    assert new_input == "", "New input should be empty"
    assert app.Workflow.model_validate_json(output), "Output should be a valid Workflow"
    assert workflow.name, "Workflow name should not be empty"
    assert len(workflow.steps) == 2, "Workflow should have two steps"


def test_update__invalid_workflow():
    """Test the update function (error: invalid workflow)."""
    # given
    output = '{"name": 1}'
    # when
    with pytest.raises(gr.Error) as error:
        app.update(output=output)
    # then
    assert "2 validation errors for Workflow" in str(error.value), (
        "Error value should have 2 validation errors"
    )
    assert error.value.title == "Workflow Update Error", "Error value should have a title."  # ty: ignore[unresolved-attribute]


def test_update():
    """Test the update function."""
    # given
    output = """
        {
            "name": "Remove background",
            "steps": [
                {
                    "title": "Remove Background",
                    "prompt": "Remove the background from the image."
                }
            ]
        }
    """
    # when
    workflow = app.update(output=output)
    # then
    assert workflow.name == "Remove background", "Workflow name should be set"
    assert len(workflow.steps) == 1, "Workflow should have one step"


def test_execute():
    """Test the execute function."""
    # given
    image = Image.open("images/picture.png")
    workflow = app.Workflow(
        name="Test Workflow",
        steps=[
            app.Step(title="Convert to red", prompt="Change the product color to red."),
            app.Step(title="Put in forest", prompt="Put the product in a forest environment."),
        ],
    )

    # when
    *_, (last_progress, last_gallery) = app.execute(image=image, workflow=workflow)
    # then
    assert "Test Workflow" in last_progress, "Last progress should contain the workflow name"
    assert "Convert to red" in last_progress, "Last progress should contain 1st step title"
    assert "Put in forest" in last_progress, "Last progress should contain 2nd step title"
    assert len(last_gallery) == 2, "Last gallery should contain 2 images"
