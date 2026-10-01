"""Build the profile's project banners, including their mobile layouts.

    python3 .github/scripts/build_banners.py

The banners are SVG, so no image converters or project checkouts are needed.
Product screenshots stay separate and are not modified by this script.
"""

from build_static import project_outputs, write_outputs


if __name__ == "__main__":
    write_outputs(project_outputs())
