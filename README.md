# Tenno Flip

Greatings Tenno! 👋

This is just a simple tool I made to help with market flipping and checking item prices without having twenty browser tabs open. It uses Warframe Market API to get data.

## What it does

- **Set Details**: Shows the price of full sets versus individual parts.
- **Arcane Details**: Shows Arcane prices for both unranked and max-ranked versions.
- **Arcane Calculator**: Calculates the "Expected Value" of Arcane packs.
- **Fast**: It saves data locally so it doesn't take forever to load every time you click something.

## How to run it

1. Download the `TennoFlip.exe` file.
2. Double click it.
3. Wait a sec for it to load.
4. Profit.

## How it works

- **Average Price Calculation**: 
  - **Regular Items**: It looks at the **cheapest 5** sell orders from players who are currently online or in-game and averages them.
  - **Arcanes**: Because some arcanes don't have enough sell orders, it looks at a wider range of sell orders (including offline orders) and filters out the absolute cheapest outliers (which are often fake or snipe prices) to give you a more accurate market value.
- **Expected Value For Arcane Packs**: It multiplies the probability of getting each arcane by its calculated market price to show you the theoretical return on investment.

## Pro Tips

- **Data Folder**: The app creates a `cache` file where it stores a local database (cache). **Do not delete this** unless you want the app to run slow while it re-downloads everything. This cache makes searching instant.

## Known Issues

- **Peculiar Mods**: You might see "Peculiar" mods showing up in the Arcane list. This is because Warframe Market's API labels them as both mods and arcanes. I decided not to hard-code a fix for this, assuming they'll eventually sort it out on their end.

## Important

I made this for fun. If something breaks, let me know!

*Happy trading!*
