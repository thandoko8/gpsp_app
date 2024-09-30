from .main_scraping import scraping_from_l1b
from .predict_process import predict_process

def main_process(l1bfile):
    scraping_from_l1b(f"data_input/{l1bfile}")
    predict_process(l1bfile)
    print("Process Done")