#include <iostream>
#include <vector>
#include <fstream>
#include <algorithm>
#include <filesystem>

#define MAX_WIDTH 10000000
#define MAX_HEIGHT 100

// Represents a part of a tile
struct TilePart {
    int width, height, offsetX, offsetY;
    TilePart(int w, int h, int dx, int dy) : width(w), height(h), offsetX(dx), offsetY(dy) {}
};

// Represents a tile consisting of multiple parts
class Tile {
public:
    std::vector<TilePart> parts;

    explicit Tile(const std::vector<TilePart>& p) : parts(p) {}

    // Function to print the tile's parts
    void print() const {
        std::cout << "Tile with " << parts.size() << " parts:\n";
        for (const auto& part : parts) {
            std::cout << "  Width: " << part.width
                      << ", Height: " << part.height
                      << ", OffsetX: " << part.offsetX
                      << ", OffsetY: " << part.offsetY << '\n';
        }
    }
};

// Reads tiles from a file and stores them in a vector
int readTiles(const std::string& filename, std::vector<Tile>& tiles) {
    std::ifstream file(filename);
    if (!file) {
        std::cerr << "Failed to open file: " << filename << '\n';
        return -1;
    }

    int partCount;
    while (file >> partCount) {
        std::vector<TilePart> parts;
        for (int i = 0; i < partCount; ++i) {
            int width, height, offsetX, offsetY;
            if (!(file >> width >> height >> offsetX >> offsetY)) {
                std::cerr << "Error reading tile part data.\n";
                return -1;
            }
            parts.emplace_back(width, height, offsetX, offsetY);
        }
        tiles.emplace_back(parts);
    }

    return 0;
}

// Represents a placed tile with its position on the grid
struct PlacedTile {
    int positionX;
    Tile tile;

    PlacedTile(int x, Tile t) : positionX(x), tile(t) {}
};

// TilePacker class handles tile packing
class TilePacker {
private:
    std::vector<Tile> tiles;
    std::vector<std::vector<int>> grid;
    std::vector<PlacedTile> placedTiles;  // Store information about placed tiles
    int boundingWidth = 0;
    int boundingHeight = 0;

public:
    explicit TilePacker(const std::vector<Tile>& t) : tiles(t) {
        grid.resize(MAX_HEIGHT, std::vector<int>(MAX_WIDTH, 0));
        calculateBoundingHeight();
    }

    void calculateBoundingHeight() {
        for (const auto& tile : tiles) {
            for (const auto& part : tile.parts) {
                boundingHeight = std::max(boundingHeight, part.offsetY + part.height);
            }
        }
    }

    bool fits(int x, const Tile& tile) {
        for (const auto& part : tile.parts) {
            int w = part.width, h = part.height, dx = part.offsetX, dy = part.offsetY;
            if (x + dx + w > MAX_WIDTH) return false;

            for (int row = dy; row < dy + h; ++row) {
                for (int col = x + dx; col < x + dx + w; ++col) {
                    if (grid[row][col] == 1) {  // Space is occupied
                        return false;
                    }
                }
            }
        }
        return true;
    }

    int placeTile(const Tile& tile) {
        for (int x = 0; x < MAX_WIDTH; ++x) {
            if (fits(x, tile)) {
                for (const auto& part : tile.parts) {
                    for (int row = part.offsetY; row < part.offsetY + part.height; ++row) {
                        for (int col = x + part.offsetX; col < x + part.offsetX + part.width; ++col) {
                            grid[row][col] = 1;  // Mark the space as occupied
                        }
                    }
                }

                // Record the placed tile and its position
                placedTiles.emplace_back(x, tile);
                return x;  // Return the x position where the tile was placed
            }
        }
        return -1;  // Tile could not be placed
    }

    void packTiles() {
        for (const auto& tile : tiles) {
            int x_position = placeTile(tile);
            if (x_position == -1) {
                std::cerr << "Error: Tile doesn't fit, increase grid size.\n";
                break;
            }

            for (const auto& part : tile.parts) {
                boundingWidth = std::max(boundingWidth, x_position + part.offsetX + part.width);
            }
        }
    }

    void drawPacking() const {
        std::cout << "Packing visualization:\n";
        for (int i = 0; i < boundingHeight; ++i) {
            for (int j = 0; j < boundingWidth; ++j) {
                std::cout << (grid[i][j] ? "#" : ".");
            }
            std::cout << '\n';
        }
        std::cout << "Bounding width: " << boundingWidth << '\n';
    }

    void printPlacedTiles() const {
        std::cout << "Placed Tiles (x, tiles):\n";
        for (const auto& placedTile : placedTiles) {
            std::cout << "x = " << placedTile.positionX << ", Tile:\n";
            placedTile.tile.print();  // Print the details of the placed tile
        }
    }

    // Export the placed tiles to a file
    void exportPlacedTiles(const std::string& filename) const {
        std::ofstream outFile(filename);
        if (!outFile) {
            std::cerr << "Failed to open file for writing: " << filename << '\n';
            return;
        }
    
        // Export the bounding width
        outFile << "Bounding Width: " << boundingWidth << '\n';
    
        // Export the placed tiles
        for (const auto& placedTile : placedTiles) {
            outFile << placedTile.positionX << " ";  // x-coordinate of the placement
            for (const auto& part : placedTile.tile.parts) {
                outFile << part.width << " "
                        << part.height << " "
                        << part.offsetX << " "
                        << part.offsetY << " ";  // Part details
            }
            outFile << '\n';  // New line after each tile
        }
    
        std::cout << "Placed tiles and bounding width exported to: " << filename << '\n';
    }    
};

int main() {
    std::vector<Tile> tiles;

    // Output the current working directory
    std::filesystem::path currentPath = std::filesystem::current_path();
    std::cout << "Current working directory: " << currentPath << '\n';

    // Read tile data from file in parent directory
    const char* input_file = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\test_tiles.txt";
    if (readTiles(input_file, tiles) != 0) {
        return -1;
    }

    // Print the tiles after reading
    std::cout << "Tiles read from the file:\n";
    for (size_t i = 0; i < tiles.size(); ++i) {
        std::cout << "Tile " << i + 1 << ":\n";
        tiles[i].print();  // Print the current tile's parts
        std::cout << '\n';
    }

    // Initialize tile packer and pack the tiles
    TilePacker packer(tiles);
    packer.packTiles();

    // Visualize the packed tiles
    packer.drawPacking();

    // Print the details of the placed tiles
    packer.printPlacedTiles();
    const char* output_path = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\placed_tiles.txt";
    // Export placed tiles to a file
    packer.exportPlacedTiles(output_path);

    return 0;
}

// extern "C" __declspec(dllexport) int run_packing(const char* filename) {
//     std::vector<Tile> tiles;

//     // Output the current working directory
//     std::filesystem::path currentPath = std::filesystem::current_path();
//     std::cout << "Current working directory: " << currentPath << '\n';

//     // Read tile data from file in parent directory
//     if (readTiles("../../test_tiles.txt", tiles) != 0) {
//         return -1;
//     }

//     // Print the tiles after reading
//     std::cout << "Tiles read from the file:\n";
//     for (size_t i = 0; i < tiles.size(); ++i) {
//         std::cout << "Tile " << i + 1 << ":\n";
//         tiles[i].print();  // Print the current tile's parts
//         std::cout << '\n';
//     }

//     // Initialize tile packer and pack the tiles
//     TilePacker packer(tiles);
//     packer.packTiles();

//     // Visualize the packed tiles
//     packer.drawPacking();

//     // Print the details of the placed tiles
//     packer.printPlacedTiles();

//     // Export placed tiles to a file
//     packer.exportPlacedTiles(filename);

//     return 0;
// }
