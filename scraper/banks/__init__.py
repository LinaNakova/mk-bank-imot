"""Registry of bank adapters. Each module exposes NAME and scrape(session)."""
from . import (
    halkbank, unibank, sparkasse, srb, ttk, ccbank, pcb,  # plain HTTP + PDF
    stb, kb, altabanka,                                    # headless browser
)

ADAPTERS = [halkbank, unibank, sparkasse, srb, ttk, ccbank, pcb, stb, kb, altabanka]
