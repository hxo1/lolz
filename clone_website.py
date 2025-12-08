#!/usr/bin/env python3
"""
Website cloner that downloads HTML and all associated assets
"""

import os
import re
import sys
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
import requests
from bs4 import BeautifulSoup

class WebsiteCloner:
    def __init__(self, url, output_dir):
        self.url = url
        self.output_dir = Path(output_dir)
        self.downloaded = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_local_path(self, url):
        """Convert URL to local file path"""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # If path is empty or ends with /, use index.html
        if not path or path.endswith('/'):
            path = os.path.join(path, 'index.html')
        
        return path
    
    def download_file(self, url, local_path):
        """Download a file from URL to local path"""
        if url in self.downloaded:
            return True
            
        try:
            print(f"Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            full_path = self.output_dir / local_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write binary content
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded.add(url)
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def update_urls_in_html(self, html_content, base_url):
        """Update URLs in HTML to use relative paths"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Download and update all assets
        assets = []
        
        # CSS files (link tags)
        for link in soup.find_all('link', href=True):
            if link.get('rel') and 'stylesheet' in link.get('rel'):
                assets.append((link, 'href'))
        
        # JavaScript files
        for script in soup.find_all('script', src=True):
            assets.append((script, 'src'))
        
        # Images
        for img in soup.find_all('img', src=True):
            assets.append((img, 'src'))
        
        # Favicon and other link resources
        for link in soup.find_all('link', href=True):
            if link.get('rel') and 'icon' in str(link.get('rel')).lower():
                assets.append((link, 'href'))
        
        # Source tags (for picture elements)
        for source in soup.find_all('source', src=True):
            assets.append((source, 'src'))
        for source in soup.find_all('source', srcset=True):
            assets.append((source, 'srcset'))
        
        # Video and audio sources
        for media in soup.find_all(['video', 'audio'], src=True):
            assets.append((media, 'src'))
        
        # Background images and other URLs in style attributes
        for tag in soup.find_all(style=True):
            style = tag['style']
            urls = re.findall(r'url\([\'"]?([^\'"()]+)[\'"]?\)', style)
            for url in urls:
                full_url = urljoin(base_url, url)
                local_path = self.get_local_path(full_url)
                self.download_file(full_url, local_path)
                tag['style'] = tag['style'].replace(url, local_path)
        
        # Process all found assets
        for tag, attr in assets:
            original_url = tag[attr]
            
            # Handle srcset which can have multiple URLs
            if attr == 'srcset':
                srcset_parts = []
                for part in original_url.split(','):
                    part = part.strip()
                    if ' ' in part:
                        url, descriptor = part.rsplit(' ', 1)
                    else:
                        url, descriptor = part, ''
                    
                    full_url = urljoin(base_url, url.strip())
                    local_path = self.get_local_path(full_url)
                    self.download_file(full_url, local_path)
                    
                    if descriptor:
                        srcset_parts.append(f"{local_path} {descriptor}")
                    else:
                        srcset_parts.append(local_path)
                
                tag[attr] = ', '.join(srcset_parts)
            else:
                full_url = urljoin(base_url, original_url)
                local_path = self.get_local_path(full_url)
                
                # Download the asset
                self.download_file(full_url, local_path)
                
                # Update the URL to relative path
                tag[attr] = local_path
        
        return str(soup)
    
    def process_css(self, css_content, css_url):
        """Process CSS to download referenced assets"""
        # Find all url() references in CSS
        urls = re.findall(r'url\([\'"]?([^\'"()]+)[\'"]?\)', css_content)
        
        for url in urls:
            # Skip data URIs
            if url.startswith('data:'):
                continue
            
            full_url = urljoin(css_url, url)
            local_path = self.get_local_path(full_url)
            
            # Download the asset
            if self.download_file(full_url, local_path):
                # Update the CSS with relative path
                css_content = css_content.replace(url, local_path)
        
        return css_content
    
    def clone(self):
        """Main method to clone the website"""
        try:
            print(f"Fetching main page: {self.url}")
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            # Get the HTML content
            html_content = response.text
            
            # Update URLs and download assets
            updated_html = self.update_urls_in_html(html_content, self.url)
            
            # Save the main HTML file
            main_file = self.output_dir / 'index.html'
            main_file.parent.mkdir(parents=True, exist_ok=True)
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(updated_html)
            
            print(f"\nSuccessfully cloned website to {self.output_dir}")
            print(f"Total files downloaded: {len(self.downloaded) + 1}")
            print(f"\nYou can view the website by opening: {main_file}")
            
            # Process CSS files to download fonts and images referenced in them
            css_files = list(self.output_dir.glob('**/*.css'))
            for css_file in css_files:
                try:
                    with open(css_file, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    
                    # Construct the original CSS URL
                    relative_path = css_file.relative_to(self.output_dir)
                    css_url = urljoin(self.url, str(relative_path))
                    
                    # Process and update CSS
                    updated_css = self.process_css(css_content, css_url)
                    
                    with open(css_file, 'w', encoding='utf-8') as f:
                        f.write(updated_css)
                except Exception as e:
                    print(f"Error processing CSS file {css_file}: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error cloning website: {e}")
            return False

def main():
    url = "https://o9yan5y22t22lhvi0rtj8hq25tbkzanz.oastify.com/"
    output_dir = "/projects/sandbox/lolz/website"
    
    cloner = WebsiteCloner(url, output_dir)
    success = cloner.clone()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
