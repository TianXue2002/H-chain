#include <iostream>
#include <vector>
#include <fstream>
#include <algorithm>
#include <sstream>
#include <climits>

#define MAX_WIDTH 1000000
#define MAX_HEIGHT 100

struct TilePart {
    int width, height, offsetX, offsetY;
    TilePart(int w, int h, int dx, int dy) : width(w), height(h), offsetX(dx), offsetY(dy) {}
};

class Tile {
public:
    std::vector<TilePart> parts;
    bool isPreplaced;
    int positionX;  // Absolute x position for preplaced tiles or placed free tiles

    explicit Tile(const std::vector<TilePart>& p, bool preplaced = false, int x = 0)
        : parts(p), isPreplaced(preplaced), positionX(x) {}

    void print() const {
        std::cout << (isPreplaced ? "Preplaced" : "Movable") << " tile";
        if (isPreplaced) std::cout << " at x=" << positionX;
        std::cout << " with " << parts.size() << " parts:\n";
        for (const auto& part : parts) {
            std::cout << "  " << part.width << "x" << part.height 
                      << " at offset (" << part.offsetX << "," << part.offsetY << ")\n";
        }
    }

    int getTotalWidth() const {
        int maxX = 0;
        for (const auto& part : parts) {
            maxX = std::max(maxX, part.offsetX + part.width);
        }
        return maxX;
    }

    int getTotalHeight() const {
        int maxY = 0;
        for (const auto& part : parts) {
            maxY = std::max(maxY, part.offsetY + part.height);
        }
        return maxY;
    }
};

class TilePacker {
private:
    std::vector<std::vector<bool>> grid;
    std::vector<Tile> placedTiles;
    int boundingWidth = 0;
    int boundingHeight = 0;

    void initializeGrid() {
        grid.resize(MAX_HEIGHT, std::vector<bool>(MAX_WIDTH, false));
    }

    bool fits(int x, const Tile& tile) const {
        for (const auto& part : tile.parts) {
            int endX = x + part.offsetX + part.width;
            int endY = part.offsetY + part.height;

            if (endX > MAX_WIDTH || endY > MAX_HEIGHT) {
                return false;
            }

            for (int row = part.offsetY; row < endY; ++row) {
                for (int col = x + part.offsetX; col < endX; ++col) {
                    if (grid[row][col]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    void markOccupied(int x, const Tile& tile) {
        for (const auto& part : tile.parts) {
            for (int row = part.offsetY; row < part.offsetY + part.height; ++row) {
                for (int col = x + part.offsetX; col < x + part.offsetX + part.width; ++col) {
                    grid[row][col] = true;
                }
            }
            boundingHeight = std::max(boundingHeight, part.offsetY + part.height);
        }
    }

    bool doesTileCollideWithOthers(const Tile& tile) {
        for (const auto& otherTile : placedTiles) {
            if (&otherTile != &tile) {  // Skip the tile itself
                // Check for potential overlap by comparing bounding boxes
                for (const auto& part : tile.parts) {
                    int endX = tile.positionX + part.offsetX + part.width;
                    int endY = part.offsetY + part.height;

                    for (const auto& otherPart : otherTile.parts) {
                        int otherEndX = otherTile.positionX + otherPart.offsetX + otherPart.width;
                        int otherEndY = otherPart.offsetY + otherPart.height;

                        // Check for overlap: if any part overlaps, return true
                        if (!(endX <= otherTile.positionX + otherPart.offsetX || 
                              tile.positionX + part.offsetX >= otherEndX || 
                              endY <= otherPart.offsetY || 
                              part.offsetY >= otherEndY)) {
                            return true; // Collision detected
                        }
                    }
                }
            }
        }
        return false;  // No collision
    }

    void updateGridAfterMove() {
        // Reinitialize the grid
        for (int i = 0; i < MAX_HEIGHT; ++i) {
            std::fill(grid[i].begin(), grid[i].end(), false);
        }

        // Mark occupied grid cells based on the new positions of the placed tiles
        for (const auto& tile : placedTiles) {
            if (tile.isPreplaced) {
                markOccupied(tile.positionX, tile);  // Mark the grid for preplaced tiles
            }
        }
    }

    // Function to push preplaced tiles dynamically to optimize packing
    void pushPreplacedTiles(Tile& newTile) {
        std::cout << "Pushing preplaced tiles to optimize packing for the new tile...\n";
        bool tileMoved = false;

        // Try to push preplaced tiles forward to make room for the new tile
        for (auto& tile : placedTiles) {
            if (tile.isPreplaced && tile.positionX + tile.getTotalWidth() > newTile.positionX) {
                int moveDistance = newTile.positionX - (tile.positionX + tile.getTotalWidth());

                if (moveDistance > 0) {
                    std::cout << "Pushing tile at position " << tile.positionX 
                              << " forward by " << moveDistance << " units.\n";
                    tile.positionX += moveDistance;
                    tileMoved = true;
                }
            }
        }

        // Update grid after tile pushing
        if (tileMoved) {
            updateGridAfterMove();
        }
    }

public:
    TilePacker() {
        initializeGrid();
    }

    void addPreplacedTile(int x, int w, int h, int dx, int dy) {
        std::vector<TilePart> parts;
        parts.emplace_back(w, h, dx, dy);
        Tile tile(parts, true, x);
        markOccupied(x, tile);
        boundingWidth = std::max(boundingWidth, x + tile.getTotalWidth());
        placedTiles.push_back(tile);
    }

    bool placeFreeTile(const std::vector<TilePart>& parts) {
        Tile newTile(parts);

        // Push preplaced tiles before trying to place a new free tile
        pushPreplacedTiles(newTile);

        for (int x = 0; x <= MAX_WIDTH - newTile.getTotalWidth(); ++x) {
            if (fits(x, newTile)) {
                markOccupied(x, newTile);
                boundingWidth = std::max(boundingWidth, x + newTile.getTotalWidth());
                newTile.positionX = x; // Record the position of the free tile
                placedTiles.push_back(newTile);
                return true;
            }
        }
        return false;
    }

    void movePreplacedTile(int x, int a) {
        std::cout << "Attempting to push preplaced tile at position " << x << " by " << a << " units.\n";

        for (auto& tile : placedTiles) {
            if (tile.positionX == x && tile.isPreplaced) {
                int newPosition = tile.positionX + a;

                Tile tempTile = tile;
                tempTile.positionX = newPosition;

                if (!doesTileCollideWithOthers(tempTile)) {
                    std::cout << "Tile at position " << x << " can be pushed. Moving it to position " << newPosition << ".\n";
                    tile.positionX = newPosition;

                    for (auto& otherTile : placedTiles) {
                        if (otherTile.positionX >= x && &otherTile != &tile) {
                            otherTile.positionX += a;
                        }
                    }

                    updateGridAfterMove();
                    std::cout << "Grid updated after move.\n";
                    return;
                } else {
                    std::cout << "Cannot push tile at position " << x << " due to collision.\n";
                }
            }
        }
    }

    void loadPreplacedTiles(const std::string& filename) {
        std::ifstream file(filename);
        if (!file) {
            std::cerr << "Failed to open preplaced tiles file: " << filename << "\n";
            return;
        }

        std::string line;
        while (std::getline(file, line)) {
            if (line.empty()) continue;

            std::istringstream iss(line);
            int x, w, h, dx, dy;
            if (iss >> x >> w >> h >> dx >> dy) {
                addPreplacedTile(x, w, h, dx, dy);
            } else {
                std::cerr << "Invalid preplaced tile format: " << line << "\n";
            }
        }
    }

    void loadFreeTiles(const std::string& filename) {
        std::ifstream file(filename);
        if (!file) {
            std::cerr << "Failed to open free tiles file: " << filename << "\n";
            return;
        }

        std::string line;
        while (std::getline(file, line)) {
            if (line.empty()) continue;

            int partCount;
            std::istringstream iss(line);
            if (!(iss >> partCount)) {
                std::cerr << "Invalid part count: " << line << "\n";
                continue;
            }

            if (!std::getline(file, line)) {
                std::cerr << "Unexpected end of file after part count\n";
                break;
            }

            std::istringstream partIss(line);
            int w, h, dx, dy;
            if (partIss >> w >> h >> dx >> dy) {
                std::vector<TilePart> parts;
                parts.emplace_back(w, h, dx, dy);
                if (!placeFreeTile(parts)) {
                    std::cerr << "Failed to place free tile: ";
                    for (const auto& part : parts) {
                        std::cerr << part.width << "x" << part.height << " ";
                    }
                    std::cerr << "\n";
                }
            } else {
                std::cerr << "Invalid tile part format: " << line << "\n";
            }
        }
    }

    void visualize(int maxRows = 20, int maxCols = 80) const {
        std::cout << "Packing visualization (" << boundingWidth << "x" << boundingHeight << "):\n";
        int rowsToShow = std::min(boundingHeight, maxRows);
        int colsToShow = std::min(boundingWidth, maxCols);

        for (int y = 0; y < rowsToShow; ++y) {
            for (int x = 0; x < colsToShow; ++x) {
                std::cout << (grid[y][x] ? '#' : '.');
            }
            std::cout << "\n";
        }
    }

    void exportResults(const std::string& filename) const {
        std::ofstream out(filename);
        if (!out) {
            std::cerr << "Failed to open output file: " << filename << "\n";
            return;
        }

        out << "Bounding Width: " << boundingWidth << "\n";
        out << "Bounding Height: " << boundingHeight << "\n";
        
        for (const auto& tile : placedTiles) {
            if (tile.isPreplaced) {
                out << "Preplaced " << tile.positionX << " ";
            } else {
                out << "Placed " << tile.positionX << " ";
            }
            for (const auto& part : tile.parts) {
                out << part.width << " " << part.height << " "
                    << part.offsetX << " " << part.offsetY << " ";
            }
            out << "\n";
        }
    }
};

int main() {
    TilePacker packer;

    // Load preplaced tiles (format: Position_x, width, height, dx, dy)
    const char* preplaced_tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\moved_place_tiles.txt";
    packer.loadPreplacedTiles(preplaced_tiles);

    // Load free tiles (format: part_count followed by width, height, dx, dy)
    const char* free_tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\test_tiles.txt";
    packer.loadFreeTiles(free_tiles);
    // Visualize the packing (showing first 20 rows and 80 columns)
    packer.visualize();

    // Export results
    const char* result_tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\all_tiles.txt";
    packer.exportResults(result_tiles);

    std::cout << "Packing completed. Results saved to packing_results.txt\n";
    return 0;
}