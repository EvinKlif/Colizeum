from playwright.async_api import async_playwright
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from tqdm import tqdm
import config


class ProcessorModelMapper:


    PROCESSOR_PREFIXES = {
        "AMD Ryzen": "Ryzen",
        "Intel Core": "Core",
        "AMD A": "A",
        "Intel Pent": "Pentium Gold",
        "Intel Cel": "Celeron",
        "AMD Athl": "Athlon"
    }

    @staticmethod
    def process_model(processor_name: str) -> str:
        clean_name = processor_name.replace("Процессор ", "").split(",")[0].strip()
        for prefix, replacement in ProcessorModelMapper.PROCESSOR_PREFIXES.items():
            if clean_name.startswith(prefix):
                model_part = clean_name[len(prefix):].strip()
                if model_part and replacement[-1].isalpha() and model_part[0].isdigit():
                    model_part = " " + model_part
                return (replacement + model_part).strip()
        return clean_name


class WebScraper:
    BASE_URL = "https://www.citilink.ru"
    PRODUCTS_PAGE = "/catalog/processory/"
    REFERENCE_PARAM = "?ref=undefined"

    async def fetch_dynamic_page(self, page_number: int) -> str:
        """Получение содержимого динамической страницы"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            url = f"{self.BASE_URL}{self.PRODUCTS_PAGE}{self.REFERENCE_PARAM}&p={page_number}"
            await page.goto(url)
            await page.wait_for_timeout(5000)

            html_content = await page.content()
            await browser.close()
            return html_content


class ProcessorDataExtractor:
    PRICE_ELEMENT_CLASS = (
        "e59n8xw0 app-catalog-4zpz15-StyledGridItem--StyledGridItem-GridItem--WrappedGridItem "
        "e1uawgvp0"
    )
    PRICE_SPAN_CLASS = (
        "e4ahr150 e1a7a4n70 app-catalog-1dno20p-StyledTypography--getTypographyStyle-composeBreakpointsStyles--arrayOfStylesByBreakpoints-StyledText--getTextStyle-Text--StyledTextComponent-MainPriceNumber--StyledMainPriceNumber ez8h4tf0"
    )
    NAME_LINK_CLASS = "app-catalog-1g0fl7h-Anchor--Anchor-Anchor--StyledAnchor ejir1360"

    def __init__(self):
        self.model_mapper = ProcessorModelMapper()

    def extract_processor_data(self, html_content: str) -> List[Dict]:
        soup = BeautifulSoup(html_content, 'html.parser')
        processors_data = []
        price_elements = soup.find_all('div', class_=self.PRICE_ELEMENT_CLASS)

        for element in price_elements:
            try:
                price_span = element.find('span', class_=self.PRICE_SPAN_CLASS)
                if not price_span:
                    continue

                price_number = int(price_span.get_text().strip().replace(' ', ''))

                name_link = element.find('a', class_=self.NAME_LINK_CLASS)
                if not name_link:
                    continue

                processor_name = name_link.get_text().strip()

                if 'Intel' in processor_name:
                    processed_name = self.model_mapper.process_model(processor_name)
                    processors_data.append({
                        "Производитель": 'Intel',
                        "Модель": processed_name,
                        "Цена": price_number
                    })

                elif 'AMD' in processor_name:
                    processed_name = self.model_mapper.process_model(processor_name)
                    processors_data.append({
                        "Производитель": 'AMD',
                        "Модель": processed_name,
                        "Цена": price_number
                    })

            except (ValueError, AttributeError):
                continue

        return processors_data


class GoogleSheetsUploader:
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    SPREADSHEET_NAME = config.spreadsheet_name_table

    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            'credentials.json',
            scopes=self.SCOPES
        )
        self.client = gspread.authorize(self.credentials)

    def upload_data(self, data: List[Dict]) -> None:
        sheet = self.client.open(self.SPREADSHEET_NAME).sheet1

        sorted_data = sorted(data, key=lambda x: x['Цена'], reverse=True)

        df = pd.DataFrame(sorted_data)

        sheet.clear()
        data_to_upload = [df.columns.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)


class ProcessorScraperPipeline:
    def __init__(self):
        self.scraper = WebScraper()
        self.data_extractor = ProcessorDataExtractor()
        self.uploader = GoogleSheetsUploader()

    async def scrape_all_pages(self) -> List[Dict]:
        all_items = []
        page_number = 1

        with tqdm(desc="Скрапинг страниц", unit="страница") as pbar:
            while True:
                html_content = await self.scraper.fetch_dynamic_page(page_number)
                processors_data = self.data_extractor.extract_processor_data(html_content)

                if not processors_data:
                    break

                all_items.extend(processors_data)
                pbar.update(1)
                pbar.set_postfix({
                    'процессоров': len(processors_data),
                    'всего': len(all_items)
                })

                page_number += 1

        return all_items


async def main():
    pipeline = ProcessorScraperPipeline()
    processors_data = await pipeline.scrape_all_pages()
    pipeline.uploader.upload_data(processors_data)


if __name__ == "__main__":
    asyncio.run(main())