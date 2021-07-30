import keyboard
import pandas as pd
import pyautogui as ag
import pyperclip
import tabulate  # Force to include in pyinstaller

import classes

output_dataframe = pd.DataFrame()


def get_items(grid) -> pd.DataFrame:
    item_list = []
    for t in grid:
        ag.moveTo(t[0], t[1])
        keyboard.press_and_release("ctrl+c")
        try:
            item_list.append(classes.Item(pyperclip.paste()).properties)
        except IndexError:
            pass
    items = pd.DataFrame().from_records(item_list)
    items = items[["base", "Item Class"]]
    items.drop_duplicates(inplace=True)
    return items


def format_final_df(df) -> pd.DataFrame:
    new_cols = []
    for col in df.columns:
        if isinstance(col, str):
            new_cols.append(col)
        else:
            new_cols.append(f"{col[0]} {col[1]}")
    df.columns = new_cols
    df.rename(
        columns={
            "base": "Base",
            "Items sum": "Items",
            "chaosValue max": "Chaos Max",
            "chaosValue min": "Chaos Min",
            "chaosValue mean": "Chaos Average",
        },
        inplace=True,
    )
    return df[
        [
            "Base",
            "Item Class",
            "Item Level",
            "Items",
            "Chaos Min",
            "Chaos Average",
            "Chaos Max",
        ]
    ]


def display_items(
    items: pd.DataFrame,
    prices: pd.DataFrame,
    cfg: classes.Config = classes.Config().load_config(),
) -> pd.DataFrame:

    global output_dataframe
    min_chaos = float(cfg["Prices"].get("MinimumMeanChaosValue"))
    prices = prices.pivot_table(
        values=["chaosValue", "Items"],
        index="baseType",
        aggfunc={"chaosValue": ["mean", "min", "max"], "Items": "sum"},
    )
    merge = pd.merge(
        items, prices.reset_index(), left_on="base", right_on="baseType", how="left"
    )
    merge = merge.sort_values(by=("chaosValue", "mean"), ascending=False)
    merge = merge.loc[merge[("chaosValue", "mean")] >= min_chaos]
    merge = format_final_df(merge)
    output_dataframe = merge.copy()
    print(merge.to_markdown(mode="github", index=False))
    merge.to_csv("sample_df.csv", index=False)


def main() -> None:
    cfg = classes.Config().load_config()
    ag.PAUSE = float(cfg["Base"].get("MouseMoveDelay"))
    lang = cfg["Base"].get("Language", fallback="EN")
    league = cfg["Base"].get("League")

    if cfg["Base"].get("RefreshPricesOnStart", fallback="True") == "True":
        classes.Prices().fetch_prices(league=league, language=lang)

    prices = classes.Prices().load_prices()
    continue_on_key = cfg["Base"].get("Hotkey")
    grid = classes.TradingWindow().get_grid()

    while True:
        pyperclip.copy(" ")
        print(f"Waiting for {continue_on_key} press...")
        keyboard.wait(continue_on_key)
        items = get_items(grid=grid)
        display_items(items=items, prices=prices, cfg=cfg)

output_dataframe = pd.read_csv('sample_df.csv')