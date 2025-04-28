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
        Tile tile(parts);
        for (int x = 0; x <= MAX_WIDTH - tile.getTotalWidth(); ++x) {
            if (fits(x, tile)) {
                markOccupied(x, tile);
                boundingWidth = std::max(boundingWidth, x + tile.getTotalWidth());
                tile.positionX = x; // Record the position of the free tile
                placedTiles.push_back(tile);
                return true;
            }
        }
        return false;
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

            // First line is part count (should be 1 based on your format)
            int partCount;
            std::istringstream iss(line);
            if (!(iss >> partCount)) {
                std::cerr << "Invalid part count: " << line << "\n";
                continue;
            }

            // Next line contains the part data
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
        
        // Export preplaced tiles
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

    std::cout << "Packing completed. Results saved to all_tiles.txt\n";
    return 0;
}
