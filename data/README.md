# Game Data Directory

This directory contains game content data files for offline play.

## C2C Data Files

The `c2c/` subdirectory contains XML data files from the **Caveman2Cosmos** mod for Civilization 4:
- `Technologies_CIV4TechInfos.xml` - Technology tree (943 technologies)
- `Buildings_Regular_CIV4BuildingInfos.xml` - Building definitions (2,402 buildings)

### Source
These files are automatically downloaded from the [Caveman2Cosmos GitHub repository](https://github.com/caveman2cosmos/Caveman2Cosmos) the first time you run the game.

### Offline Play
Once downloaded, these files enable the game to run completely offline. The game will:
1. Check the `data/c2c/` directory first (local data)
2. Fall back to user cache at `~/.history_idle/c2c_cache/`
3. Download from GitHub if neither is available

### Updates
To update the game data to the latest C2C version:
1. Delete the files in `data/c2c/`
2. Delete the cache at `~/.history_idle/c2c_cache/`
3. Run the game again to re-download

### File Sizes
- Technologies: ~1.1 MB
- Buildings: ~4.8 MB
- Total: ~5.9 MB

These files are included in version control to ensure the game works offline for all users immediately after cloning the repository.

## License
The C2C data files are from the Caveman2Cosmos mod and retain their original licensing. See the [C2C repository](https://github.com/caveman2cosmos/Caveman2Cosmos) for details.
