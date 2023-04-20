import random
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI
from fastapi.responses import Response, RedirectResponse
from io import BytesIO

from config import (
    ENDPOINT_PREFIX,
    API_VERSION,
    API_TITLE,
    API_DESCRIPTION,
    API_DOCS_URL,
    API_REDOC_URL,
    API_OPENAPI_URL,
    API_TERM_OF_SERVICE,
    API_CONTACT_EMAIL,
    API_WEBSITE,
    API_NAME,
    API_THUMBNAIL_MAX_HEIGHT,
    API_THUMBNAIL_MAX_WIDTH,
    API_THUMBNAIL_MIN_HEIGHT,
    API_THUMBNAIL_MIN_WIDTH,
)

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=API_DOCS_URL,
    redoc_url=API_REDOC_URL,
    openapi_url=API_OPENAPI_URL,
    terms_of_service=API_TERM_OF_SERVICE,
    contact={
        "name": API_NAME,
        "url": API_WEBSITE,
        "email": API_CONTACT_EMAIL,
    },
)


def generate_gradient(
    width: int, height: int, color1: tuple[int, int, int], color2: tuple[int, int, int]
) -> Image:
    """
    Generates an image with a vertical gradient of the given width and height using the two given colors.

    :param width: The width of the image.
    :param height: The height of the image.
    :param color1: The starting color of the gradient as a tuple of three integers (r, g, b).
    :param color2: The ending color of the gradient as a tuple of three integers (r, g, b).
    :return: An Image object containing the generated gradient.
    """
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        r = y / height
        color = tuple(int(color1[i] * (1 - r) + color2[i] * r) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    return image


def add_text_to_image(image: Image, text: str, width: int, height: int) -> Image:
    """
    Adds the given text to the center of the given image.

    :param image: The image to add text to.
    :param text: The text to add.
    :param width: The width of the image.
    :param height: The height of the image.
    :return: An Image object with the text added to the center.
    """

    def get_font_size(text: str) -> int:
        """
        Calculates the appropriate font size for the given text.

        :param text: The text to calculate the font size for.
        :return: The appropriate font size as an integer.
        """
        length = len(text)
        font_size = int(100 / (1 + 0.05 * abs(20 - length)))
        return font_size

    font_size = get_font_size(text)
    font = ImageFont.truetype("Arial Bold.ttf", font_size, encoding="unic")
    draw = ImageDraw.Draw(image)
    text_width, text_height = draw.textsize(text, font=font)
    position = ((width - text_width) / 2, (height - text_height) / 2)
    draw.text(
        position, text, fill="white", font=font, stroke_width=3, stroke_fill="black"
    )
    return image


@app.get(ENDPOINT_PREFIX + "{text}.png")
@app.head(ENDPOINT_PREFIX + "{text}.png", include_in_schema=False)
def get_thumbnail(
    width: int = 1200,
    height: int = 630,
    top_color: str = None,
    bottom_color: str = None,
    text: str = None,
) -> Response:
    """
    Generates a vertical gradient image with the given width, height, top color, bottom color, and text.

    - The width and height must be integers.
    - Top color and bottom color must be hex color codes.
    - Text must be a string.
    """
    # Make sure the width and height are within the allowed range.
    if width <= API_THUMBNAIL_MIN_WIDTH or width >= API_THUMBNAIL_MAX_WIDTH:
        # choose maximum width if width is too large
        distance_from_max_width = abs(width - API_THUMBNAIL_MAX_WIDTH)
        # choose minimum width if width is too small
        distance_from_min_width = abs(width - API_THUMBNAIL_MIN_WIDTH)
        if distance_from_max_width < distance_from_min_width:
            width = API_THUMBNAIL_MAX_WIDTH
        else:
            width = API_THUMBNAIL_MIN_WIDTH

    if height <= API_THUMBNAIL_MIN_HEIGHT or height >= API_THUMBNAIL_MAX_HEIGHT:
        # choose maximum height if height is too large
        distance_from_max_height = abs(height - API_THUMBNAIL_MAX_HEIGHT)
        # choose minimum height if height is too small
        distance_from_min_height = abs(height - API_THUMBNAIL_MIN_HEIGHT)
        if distance_from_max_height < distance_from_min_height:
            height = API_THUMBNAIL_MAX_HEIGHT
        else:
            height = API_THUMBNAIL_MIN_HEIGHT

    # Generate a random color if no color is specified.
    if top_color is None:
        top_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
    else:
        top_color = top_color.lstrip("#").lower()
        try:
            top_color = tuple(
                int(top_color[i : i + 2], 16) for i in (0, 2, 4)
            )  # this is a tuple comprehension for converting hex to rgb
        except ValueError:
            top_color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )

    if bottom_color is None:
        bottom_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
    else:
        bottom_color = bottom_color.lstrip("#").lower()
        try:
            bottom_color = tuple(
                int(bottom_color[i : i + 2], 16) for i in (0, 2, 4)
            )  # this is a tuple comprehension for converting hex to rgb
        except ValueError:
            bottom_color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )

    image = generate_gradient(
        width,
        height,
        top_color,
        bottom_color,
    )
    text = text.replace("_", " ").replace("-", " ")
    image = add_text_to_image(image, text, width, height)
    bytes_io = BytesIO()
    image.save(bytes_io, format="PNG")
    bytes_io.seek(0)
    return Response(content=bytes_io.read(), media_type="image/png")


# redirect any request not defined above to the root path
@app.get("/{path:path}", include_in_schema=False)
def redirect_to_root(path: str) -> RedirectResponse:
    """
    Redirects any request not defined above to the root path ("/").

    :param path: The path of the request.
    :return: A RedirectResponse object redirecting to the root path.
    """
    return RedirectResponse(API_DOCS_URL)
