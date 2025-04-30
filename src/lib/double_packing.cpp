#include <iostream>
#include <vector>
#include <fstream>
#include <algorithm>
#include <sstream>
#include <climits>
#include <cmath>



#define MAX_WIDTH 1000000
#define MAX_HEIGHT 100

struct TilePart {
    int width, height, offsetX, offsetY;
    TilePart(int w, int h, int dx, int dy) : width(w), height(h), offsetX(dx), offsetY(dy) {}
};

class Tile {
public:
    std::vector<TilePart> parts;
    bool isInter;
    int positionX;  // Absolute x position for preplaced tiles or placed free tiles
    int separation = 0;
    explicit Tile(const std::vector<TilePart>& p, bool inter = false, int x = 0)
        : parts(p), isInter(inter), positionX(x) {}

    void print() const {
        std::cout << (isInter ? "Inter" : "Movable") << " tile";
        if (isInter) std::cout << " at x=" << positionX;
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
    std::vector<std::vector<bool>> intra_grid;
    std::vector<std::vector<bool>> inter_grid;
    std::vector<Tile> placedTiles;
    int min_separation = 0;
    int boundingWidth = 0;
    int boundingHeight = 0;
    bool if_double = false;

    void initializeGrid() {
        intra_grid.resize(MAX_HEIGHT, std::vector<bool>(MAX_WIDTH, false));
        inter_grid.resize(MAX_HEIGHT, std::vector<bool>(MAX_WIDTH, false));
    }

    bool intra_fits(int x, const Tile& tile) const {
        for (const auto& part : tile.parts) {
            int endX = x + part.offsetX + part.width;
            int endY = part.offsetY + part.height;

            if (endX > MAX_WIDTH || endY > MAX_HEIGHT) {
                return false;
            }

            for (int row = part.offsetY; row < endY; ++row) {
                for (int col = x + part.offsetX; col < endX; ++col) {
                    if (intra_grid[row][col]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    bool inter_fits(int x, const Tile& tile) const {
        for (const auto& part : tile.parts) {
            int endX = x + part.offsetX + part.width + tile.separation;
            int endY = part.offsetY + part.height;

            if (endX > MAX_WIDTH || endY > MAX_HEIGHT) {
                return false;
            }

            for (int row = part.offsetY; row < endY; ++row) {
                for (int col = x + part.offsetX; col < endX; ++col) {
                    if (inter_grid[row][col]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    void intra_occupied(int x, const Tile& tile) {
        for (const auto& part : tile.parts) {
            for (int row = part.offsetY; row < part.offsetY + part.height; ++row) {
                for (int col = x + part.offsetX; col < x + part.offsetX + part.width; ++col) {
                    intra_grid[row][col] = true;
                    inter_grid[row][col] = true;
                }
            }
            boundingHeight = std::max(boundingHeight, part.offsetY + part.height);
        }
    }

    void inter_occupied(int x, const Tile& tile) {
        for (const auto& part : tile.parts) {
            for (int row = part.offsetY; row < part.offsetY + part.height; ++row) {
                // Occupied the intra grid
                for (int col = x + part.offsetX; col < x + part.offsetX + part.width; ++col) {
                    intra_grid[row][col] = true;
                }
                // Occupied the inter grid
                for (int col = x + part.offsetX; col < x + part.offsetX + part.width + tile.separation; ++col) {
                    inter_grid[row][col] = true;
                }
            }
            boundingHeight = std::max(boundingHeight, part.offsetY + part.height);
        }
    }

public:
    TilePacker() {
        initializeGrid();
    }

    void setSeparation(int sep) {
        if (sep < 0) {
            std::cerr << "Separation must be non-negative.\n";
            return;
        }
        min_separation = sep;
    }

    void setDouble(bool flag) {
        if_double = flag;
        if(if_double){
            std::cout<<"right"<<std::endl;
        }
        else{
            std::cout<<"wrong"<<std::endl;
        }
    }

    bool placeIntraTile(const std::vector<TilePart>& parts) {
        Tile tile(parts);
        for (int x = 0; x <= MAX_WIDTH - tile.getTotalWidth(); ++x) {
            if (intra_fits(x, tile)) {
                intra_occupied(x, tile);
                boundingWidth = std::max(boundingWidth, x + tile.getTotalWidth());
                tile.positionX = x; // Record the position of the free tile
                placedTiles.push_back(tile);
                return true;
            }
        }
        return false;
    }

    bool placeInterTile(const std::vector<TilePart>& parts, int max_width) {
        Tile tile(parts);
        tile.isInter = true;
        if (if_double){
            tile.separation = min_separation;
        }else{
            tile.separation = ceil(min_separation/max_width+1)*max_width;
        }
        
        for (int x = 0; x <= MAX_WIDTH - (tile.getTotalWidth() + tile.separation); ++x) {
            if (inter_fits(x, tile)) {
                inter_occupied(x, tile);
                boundingWidth = std::max(boundingWidth, x + tile.getTotalWidth()+tile.separation);
                tile.positionX = x; // Record the position of the free tile
                placedTiles.push_back(tile);
                return true;
            }
        }
        return false;
    }

    void loadTiles(const std::string& filename) {
        std::ifstream file(filename);
        if (!file) {
            std::cerr << "Failed to open free tiles file: " << filename << "\n";
            return;
        }
        int max_width = 0;
        std::string line;
        while (std::getline(file, line)) {
            if (line.empty()) continue;

            // First line: intraTile or interTile
            bool ifInter = false;
            if (line == "interTile") {
                ifInter = true;
            } else if (line == "intraTile") {
                ifInter = false;
            } else {
                std::cerr << "Unknown tile type: " << line << "\n";
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
                if (w > max_width){
                    max_width = w;
                }
                std::vector<TilePart> parts;
                parts.emplace_back(w, h, dx, dy);
                if(!ifInter){
                    if (!placeIntraTile(parts)) {
                        std::cerr << "Failed to place intra tile: ";
                        for (const auto& part : parts) {
                            std::cerr << part.width << "x" << part.height << " ";
                        }
                        std::cerr << "\n";
                    }
                } else {
                    int cur_width = 0;
                    if (if_double){
                        cur_width = min_separation;
                    }else{
                        cur_width = max_width;
                    }
                    if (!placeInterTile(parts, cur_width)) {
                        std::cerr << "Failed to place inter tile: ";
                        for (const auto& part : parts) {
                            std::cerr << part.width << "x" << part.height << " ";
                        }
                        std::cerr << "\n";
                    }
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
                std::cout << (intra_grid[y][x] ? '#' : '.');
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
            out << "Placed " << tile.positionX << " ";
            for (const auto& part : tile.parts) {
                out << part.width << " " << part.height << " "
                    << part.offsetX << " " << part.offsetY << " ";
            }
            out << "\n";
        }
    }

};

#include <iostream>
#include <fstream>
#include <string>

std::pair<int, bool> readSeparationAndFlag(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        std::cerr << "Failed to open file: " << filename << "\n";
        return {-1, false};
    }

    int separation;
    bool flag;
    file >> separation >> flag; // assumes both values are present

    if (file.fail()) {
        std::cerr << "Failed to read separation and flag from file: " << filename << "\n";
        return {-1, false};
    }

    return {separation, flag};
}


int main() {
    TilePacker packer;
    const char* separation_file = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\src\\double_packing\\tiles\\separation.txt";
    auto [min_separation, if_double] = readSeparationAndFlag(separation_file);
    std::cout<<"separation is "<< min_separation << std::endl;
    std::cout<<"double_packed is "<< if_double << std::endl;
    packer.setDouble(if_double);
    packer.setSeparation(min_separation);
    // Load intra tiles (format: Position_x, width, height, dx, dy)
    if (!if_double){
        const char* tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\src\\double_packing\\tiles\\inter_intra_tiles.txt";
        packer.loadTiles(tiles);
    }else{
        const char* tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\src\\double_packing\\tiles\\second_input_tiles.txt";
        packer.loadTiles(tiles);
    }
    

    // Load inter tiles (format: part_count followed by width, height, dx, dy)
    // Visualize the packing (showing first 20 rows and 80 columns)
    // packer.visualize();

    // Export results
    if(!if_double){
        const char* result_tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\src\\double_packing\\tiles\\result_tiles.txt";
        packer.exportResults(result_tiles);
    }else{
        const char* result_tiles = "C:\\Users\\24835\\Desktop\\homework\\uiuc\\Covey\\chem\\H-chain\\src\\double_packing\\tiles\\second_result_tiles.txt";
        packer.exportResults(result_tiles);
    }
    

    std::cout << "Packing completed. Results saved to result_tiles.txt\n";
    return 0;
}
