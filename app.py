"""Combo-Banana: Your Customizable Image Workflow with Nano Banana."""

# %% IMPORTS

import io
import logging
import os
import string
import typing as T

import google.cloud.logging as gcl
import google.genai as gg
import google.genai.types as ggt
import gradio as gr
import pydantic as pdt
from PIL import Image

# %% ENVIRONS

GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() in ("true", "1")

IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image-preview")
LANGUAGE_MODEL = os.getenv("LANGUAGE_MODEL", "gemini-2.5-flash")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

# %% CONFIGS

THEME = "soft"
TITLE = "Combo-Banana"
FAVICON = "assets/favicon.ico"
EXAMPLES = [
    "Place the sport item in an action shot with a cheering crowd.",
    "Show the sport item on a field, then in a stadium, then in a store.",
    "Create a flat-lay composition with the product and related accessories.",
    "Place the person in the picture on a beach, then underwater, then on a boat.",
    "Generate a before-and-after comparison of the person using the fitness product.",
    "Generate a lifestyle image: show a person using the product in a natural setting.",
    "Generate different angles of the product at each step: front, back, and side views.",
    "Create a social media ad: place the item in a stunning landscape, add a catchy slogan",
    "Isolate a collection of products, arrange them for a website banner, and add a title.",
    "Isolate the product, then create a diagram showing an exploded view of its components.",
]
DESCRIPTION = "Your Customizable Image Workflow with Nano Banana"
FOOTER = (
    "<center>"
    "Visit my website: <a href='https://fmind.dev'>fmind.dev</a>. <br />"
    "Social Networks: "
    "<a href='https://www.linkedin.com/in/fmind-dev/'>LinkedIn</a>, "
    "<a href='https://github.com/fmind/'>GitHub</a>, "
    "<a href='https://medium.com/@fmind'>Medium</a>, "
    "<a href='https://x.com/fmind_dev'>X</a>"
    "</center>"
)

# %% PROMPTS

DEFINE_PROMPT = string.Template("""
Generate a structured multi-step JSON workflow for an image designer from a user request.

The JSON object must contain:
- "name": A string for the workflow's title.
- "steps": A list of objects, where each object has:
  - "title": A brief, descriptive string for the step's title.
  - "prompt": A detailed string for the step's instruction.

Example User Request:
"Upscale the image, then add pop-art style, then add a designer signature"

Example JSON Output:
{
    "name": "Creative Portrait",
    "steps": [
        {
            "title": "Upscale Image",
            "prompt": "Increase the image resolution and clarity for printing."
        },
        {
            "title": "Add Pop-Art Style",
            "prompt": "Apply a vibrant pop-art filter with bold colors and sharp lines."
        },
        {
            "title": "Add Designer Signature",
            "prompt": "Overlay a designer signature in the bottom-right corner."
        }
    ]
}

The steps should be concise and accurately capture all details from the user's request.

User workflow:
$workflow
""")

# %% LOGGING

logging_client = gcl.Client()
logging_client.setup_logging(log_level=getattr(logging, LOGGING_LEVEL))

# %% MODELS

genai_client = gg.Client(
    project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION, vertexai=GOOGLE_GENAI_USE_VERTEXAI
)

# %% CLASSES


class Step(pdt.BaseModel):
    """Represents a single step in the image processing pipeline."""

    title: str = pdt.Field(
        ..., description="The concise title of the step, e.g., 'Remove Background'."
    )
    prompt: str = pdt.Field(
        ..., description="A clear, concise prompt describing the action to perform on the image."
    )


class Workflow(pdt.BaseModel):
    """Represents a complete image processing workflow."""

    name: str = pdt.Field(..., description="The name of the workflow")
    steps: list[Step] = pdt.Field(
        ..., description="A list of steps in the image processing pipeline."
    )


# %% FUNCTIONS


def define(input: str, workflow: Workflow) -> tuple[T.Literal[""], str, Workflow]:
    """Defines a new workflow based on user input.

    Args:
        input: The user's input string describing the workflow.
        workflow: The current workflow object.

    Returns:
        A tuple containing an empty string, the new workflow as a JSON string,
        and the new workflow object.

    Raises:
        gr.Error: If the model fails to generate a valid workflow.
    """
    try:
        workflow_json = workflow.model_dump_json(indent=4)
        system_instruction = DEFINE_PROMPT.substitute(workflow=workflow_json)
        config = ggt.GenerateContentConfig(
            temperature=0,
            max_output_tokens=2000,
            response_schema=Workflow,
            response_mime_type="application/json",
            system_instruction=system_instruction,
        )
        response = genai_client.models.generate_content(
            model=LANGUAGE_MODEL, config=config, contents=input
        )
        new_workflow: Workflow = T.cast(Workflow, response.parsed)
        output: str = new_workflow.model_dump_json(indent=4)
        return "", output, new_workflow
    except Exception as error:
        raise gr.Error(str(error), title="Workflow Definition Error", duration=None)


def update(output: str) -> Workflow:
    """Updates the workflow with a new user definition.

    Args:
        output: A JSON string representing the new workflow.

    Returns:
        A new Workflow object.

    Raises:
        gr.Error: If the JSON string is not a valid Workflow.
    """
    try:
        return Workflow.model_validate_json(output)
    except pdt.ValidationError as error:
        raise gr.Error(str(error), title="Workflow Update Error", duration=None)


def execute(image: Image, workflow: Workflow) -> T.Generator[tuple[str, list[Image]]]:
    """Executes the user-defined workflow on a given image.

    Args:
        image: The input image to process.
        workflow: The workflow to execute.

    Yields:
        A tuple containing the progress log, a list of generated image.

    Raises:
        gr.Error: If any step of the workflow fails.
    """
    try:
        gallery = []
        progress = io.StringIO()
        progress.write(f"# Executing Workflow: {workflow.name}\n")
        yield progress.getvalue(), gallery
        for step in workflow.steps:
            progress.write(f"- Step: {step.title} ...\n")
            yield progress.getvalue(), gallery
            config = ggt.GenerateContentConfig(
                temperature=0,
                max_output_tokens=5000,
                response_modalities=["TEXT", "IMAGE"],
            )
            response = genai_client.models.generate_content(
                model=IMAGE_MODEL, config=config, contents=[image, step.prompt]
            )
            for part in response.candidates[0].content.parts:  # ty: ignore[not-iterable, non-subscriptable]
                if part.text is not None:
                    progress.write(f"> Model: {part.text}\n")
                    yield progress.getvalue(), gallery
                elif part.inline_data is not None:
                    image = Image.open(io.BytesIO(part.inline_data.data))
                    gallery.append(image)
                    yield progress.getvalue(), gallery
        progress.write("DONE.")
        yield progress.getvalue(), gallery
    except Exception as error:
        raise gr.Error(str(error), title="Workflow Execution Error", duration=None)


# %% INTERFACES

with gr.Blocks(title=TITLE, theme=THEME, fill_width=True) as demo:
    workflow = gr.State(value=Workflow(name="Empty Workflow", steps=[]))
    gr.Markdown(value=f"# {TITLE}: {DESCRIPTION}")
    with gr.Tabs():
        with gr.Tab(label="🔀 Definition"):
            gr.Markdown(value="### 🤖 Chat to build a multi-step image workflow")
            with gr.Row():
                with gr.Column():
                    input = gr.Textbox(
                        placeholder=(
                            "e.g., make the product shot look more professional "
                            "by removing the background, then place it on a white background."
                        ),
                        label="Instructions",
                        lines=5,
                    )
                    submit = gr.Button(value="Submit")
                    examples = gr.Examples(
                        examples=[[example] for example in EXAMPLES], inputs=input
                    )
                with gr.Column():
                    output = gr.Textbox(
                        placeholder="You can paste your previous workflow directly in this area",
                        label="Workflow Definition",
                        interactive=True,
                        lines=26,
                    )
            submit.click(define, inputs=[input, workflow], outputs=[input, output, workflow])
            output.change(fn=update, inputs=output, outputs=workflow)
        with gr.Tab(label="▶️ Execution"):
            gr.Markdown(value="### 🖼️ Upload an image to trigger the workflow")
            with gr.Row():
                with gr.Column():
                    image = gr.Image(label="Upload Image", type="pil", height=350)
                    progress = gr.Textbox(
                        placeholder="Execution log will be displayed here",
                        label="Progress Log",
                        interactive=False,
                        lines=8,
                    )
                with gr.Column():
                    gallery = gr.Gallery(label="Output Images", type="pil", columns=3, height=600)
            image.input(execute, inputs=[image, workflow], outputs=[progress, gallery])
    gr.Markdown(
        value="""
        <center>
        <strong>Benefits</strong>:
        Automate repetitive image editing tasks. Tailor image workflows to your needs.
        <br />
        Explore new possibilities with AI image generation.
        Save time and resources with image processing.
        </center>
        """
    )
    gr.Markdown(value=FOOTER)

# %% ENTRYPOINTS

if __name__ == "__main__":
    demo.queue()
    demo.launch(favicon_path=FAVICON, pwa=True)
