# Website Clone

This repository contains a cloned website from `https://o9yan5y22t22lhvi0rtj8hq25tbkzanz.oastify.com/`.

## Structure

- `website/` - Contains all cloned website content
  - `index.html` - Main HTML file
  - Additional assets (CSS, JavaScript, images, fonts) if present on the original site

## Viewing the Website

To view the cloned website locally, simply open the HTML file in your web browser:

```bash
# Option 1: Open directly
open website/index.html

# Option 2: Use a simple HTTP server (recommended for complex sites)
cd website
python3 -m http.server 8000
# Then visit http://localhost:8000 in your browser
```

## Cloning Process

The website was cloned using `clone_website.py`, which:
1. Fetches the complete HTML content from the source URL
2. Parses the HTML to find all referenced assets (CSS, JavaScript, images, fonts)
3. Downloads all assets while preserving directory structure
4. Updates URLs to use relative paths for local viewing
5. Processes CSS files to download embedded resources (fonts, background images)

## Implementation Details

The cloner handles:
- HTML content and structure
- External stylesheets and scripts
- Images (img tags, picture sources, srcsets)
- Embedded resources in CSS (fonts, background images)
- Media files (video, audio)
- Favicons and other link resources
- Inline styles with url() references

All relative paths are preserved to ensure the website remains functional when viewed locally.
