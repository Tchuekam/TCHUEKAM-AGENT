import scrapy

class DirectorySpider(scrapy.Spider):
    name = "directory_spider"
    
    def __init__(self, category="restaurants", location="yaounde", *args, **kwargs):
        super(DirectorySpider, self).__init__(*args, **kwargs)
        self.category = category
        self.location = location
        
        # Multi-region directory resolver
        loc = location.lower()
        if 'cameroun' in loc or 'cameroon' in loc or 'yaounde' in loc or 'douala' in loc:
            # African target registry index
            self.start_urls = [
                f"https://www.pagesjaunesducameroun.com/recherche?q={category}&l={location}"
            ]
        else:
            # European/US fallback directories
            self.start_urls = [
                f"https://www.pagesjaunes.fr/annuaire/chercher?qu={category}&ou={location}"
            ]

    def parse(self, response):
        self.log(f"Crawling directory page: {response.url}")
        
        # 1. Parse PagesJaunes Cameroun elements
        if "cameroun" in response.url or "pagesjaunesducameroun" in response.url:
            listings = response.css('div.listing-card, div.business-item, div.result-item')
            if not listings:
                # Fallback: Parse generic structured cards
                listings = response.xpath('//div[contains(@class, "card") or contains(@class, "item")]')

            for card in listings:
                name = card.css('h2::text, h3::text, a.title::text').get()
                if not name:
                    continue
                    
                phone = card.css('span.phone::text, a[href^="tel"]::text, .phone-number::text').get()
                website = card.css('a[href^="http"]::attr(href), a.website::attr(href)').get()
                email = card.css('a[href^="mailto"]::attr(href)').get()
                
                # Clean Mailto headers
                if email:
                    email = email.replace("mailto:", "").split("?")[0].strip()

                yield {
                    "name": name.strip(),
                    "phone": phone.strip() if phone else "",
                    "email": email or "",
                    "website": website or "",
                    "source": "Scrapy Directory (Cameroun)",
                    "category": self.category.capitalize(),
                    "location": self.location.capitalize(),
                    "rating": 4.0
                }
        else:
            # 2. Parse generic international layouts
            for listing in response.css('div.business-card, article.result'):
                name = listing.css('h2.name::text, a.title-link::text').get()
                if not name:
                    continue

                phone = listing.css('.phone::text, span.tel::text').get()
                website = listing.css('a.web::attr(href)').get()
                email = listing.css('a.email::attr(href)').get()

                if email:
                    email = email.replace("mailto:", "").split("?")[0].strip()

                yield {
                    "name": name.strip(),
                    "phone": phone.strip() if phone else "",
                    "email": email or "",
                    "website": website or "",
                    "source": "Scrapy Directory (Intl)",
                    "category": self.category.capitalize(),
                    "location": self.location.capitalize(),
                    "rating": 4.5
                }
                
        # Handle pagination demo stubs
        next_page = response.css('a.next-page::attr(href), a[aria-label="Next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
