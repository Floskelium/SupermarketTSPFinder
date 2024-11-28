const TILE_SIZE = 10; // Tile size in pixels
const MAP_WIDTH = 800; // Map width in pixels
const MAP_HEIGHT = 600; // Map height in pixels
const TILE_MAP_WIDTH = 68; // Tile count horizontally
const TILE_MAP_HEIGHT = 37; // Tile count vertically

let tileMap = [];       // Store tile data for each position
let db; // SQL.js database instance

const entryPoint = { x: 14, y: 35 }; // Example entry point coordinates
const endPoint = { x: 10, y: 20 };
const itemList = [1, 4, 3, 15, 20, 12, 18]; // List of aisle IDs that contain items to pick up

const oneWayPassages = {
    // Example entry: "x,y": { dx: 1, dy: 0 } for right-only movement
};

// Initialize database and setup canvas
async function initDatabase() {
    const SQL = await initSqlJs({
        locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.9.0/${file}`
    });
    db = new SQL.Database();
    db.run("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT, aisleId INTEGER, segmentId INTEGER)");
    loadMap();
}

// Load PNG and process each pixel
function loadMap() {
    const img = new Image();
    img.src = 'file.png';
    img.onload = () => {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = MAP_WIDTH;
        tempCanvas.height = MAP_HEIGHT;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(img, 0, 0);
        const imageData = tempCtx.getImageData(0, 0, MAP_WIDTH, MAP_HEIGHT);
        processImageData(imageData);
    };
}

// Process the image data and map pixels to tiles
function processImageData(imageData) {
    tileMap = Array.from({ length: TILE_MAP_HEIGHT }, () => Array(TILE_MAP_WIDTH).fill(null));

    for (let y = 0; y < TILE_MAP_HEIGHT; y++) {
        for (let x = 0; x < TILE_MAP_WIDTH; x++) {
            const index = (y * imageData.width + x) * 4;

            const [r, g, b] = [
                imageData.data[index],
                imageData.data[index + 1],
                imageData.data[index + 2]
            ];

            const aisleId = getAisleIdFromColor(r, g, b);

            if (aisleId) {
                tileMap[y][x] = { aisleId };
            } else if (r === 255 && g >= 0 && g <= 2 && b >= 0 && b <= 2) {
                // barrier; g = x dir, b = y dir
                // [0,1,2] -= 1 -> [-1,0,1]
                const key = `${x},${y}`;
                oneWayPassages[key] = { dx: g - 1, dy: b - 1 };
            }
        }
    }
    generateSVG();
}


// Generate SVG from tile map
function generateSVG() {
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", MAP_WIDTH);
    svg.setAttribute("height", MAP_HEIGHT);

    // arrow head
    const svgDefs = document.createElementNS(svgNS, "defs");
    const marker = document.createElementNS(svgNS, "marker");
    marker.setAttribute("id", "arrowhead");
    marker.setAttribute("markerWidth", "3");
    marker.setAttribute("markerHeight", "4");
    marker.setAttribute("refX", "0.1");
    marker.setAttribute("refY", "2");
    marker.setAttribute("orient", "auto");
    const arrowPath = document.createElementNS(svgNS, "path");
    arrowPath.setAttribute("d", "M0,0 V4 L2,2 Z");
    arrowPath.setAttribute("fill", "red");
    marker.appendChild(arrowPath);
    svgDefs.appendChild(marker);
    svg.appendChild(svgDefs);

    // Group tiles into continuous rectangles per aisle
    const aisleSegments = {};

    // Group tiles by aisle ID
    for (let y = 0; y < TILE_MAP_HEIGHT; y++) {
        for (let x = 0; x < TILE_MAP_WIDTH; x++) {
            const tile = tileMap[y][x];
            if (tile && tile.aisleId) {
                const aisleId = tile.aisleId;
                if (!aisleSegments[aisleId]) aisleSegments[aisleId] = [];
                aisleSegments[aisleId].push({ x, y });
            }
        }
    }

    // Draw each aisle segment as a rectangle in the SVG
    Object.entries(aisleSegments).forEach(([aisleId, tiles]) => {
        const rectGroups = groupTilesIntoRectangles(tiles);
        rectGroups.forEach(({ x, y, width, height }) => {
            const group = document.createElementNS(svgNS, "g");
            const rect = document.createElementNS(svgNS, "rect");
            rect.setAttribute("x", x * TILE_SIZE);
            rect.setAttribute("y", y * TILE_SIZE);
            rect.setAttribute("width", width * TILE_SIZE);
            rect.setAttribute("height", height * TILE_SIZE);
            rect.setAttribute("fill", "#d9ead3");//`rgb(${aisleId * 40}, ${aisleId * 30}, ${aisleId * 20})`);
            rect.setAttribute("stroke", "#6abf60");
            group.appendChild(rect);

            const aisleName = document.createElementNS(svgNS, "text");
            const fontSize = 10;
            aisleName.setAttribute("x", (x + width / 2) * TILE_SIZE);
            aisleName.setAttribute("y", (y + height / 2) * TILE_SIZE + fontSize / 2);
            aisleName.setAttribute("fill", "black");
            aisleName.setAttribute("font-size", fontSize);
            aisleName.setAttribute("text-anchor", "middle");
            aisleName.textContent = aisleId;
            group.appendChild(aisleName);
            svg.appendChild(group);
        });
    });

    document.getElementById("mapContainer").appendChild(svg);


    drawOneWayArrows(svg, oneWayPassages);

    // Execute the function and output the final path
    //const finalPath = findPathWithItems();
    //console.log("Final path:", finalPath);
    //drawPath(svg, finalPath);
}

// Helper function to group adjacent tiles into rectangles
function groupTilesIntoRectangles(tiles) {
    const groups = [];
    const visited = new Set();

    tiles.forEach(({ x, y }) => {
        if (!visited.has(`${x}-${y}`)) {
            const rect = expandRectangle(x, y, tiles, visited);
            groups.push(rect);
        }
    });

    return groups;
}

// Expand a rectangle around adjacent tiles
function expandRectangle(x, y, tiles, visited) {
    let maxX = x;
    let maxY = y;

    tiles.forEach(({ x: tileX, y: tileY }) => {
        if (!visited.has(`${tileX}-${tileY}`) && tileX >= x && tileY >= y) {
            maxX = Math.max(maxX, tileX);
            maxY = Math.max(maxY, tileY);
            visited.add(`${tileX}-${tileY}`);
        }
    });

    return { x, y, width: maxX - x + 1, height: maxY - y + 1 };
}

// Function to draw one-way passage arrows on the SVG map
function drawOneWayArrows(svgElement, oneWayPassages) {
    for (let [key, direction] of Object.entries(oneWayPassages)) {
        const [x, y] = key.split(",").map(Number);

        const arrow = document.createElementNS("http://www.w3.org/2000/svg", "line");
        arrow.setAttribute("x1", (x + 0.5 * Math.abs(direction.dy)) * TILE_SIZE + (direction.dx < 0 ? TILE_SIZE : 0));
        arrow.setAttribute("y1", (y + 0.5 * Math.abs(direction.dx)) * TILE_SIZE + (direction.dy < 0 ? TILE_SIZE : 0));
        arrow.setAttribute("x2", (x + 0.5 * Math.abs(direction.dy)) * TILE_SIZE + (direction.dx < 0 ? TILE_SIZE : 0) + direction.dx * (TILE_SIZE * 0.6));
        arrow.setAttribute("y2", (y + 0.5 * Math.abs(direction.dx)) * TILE_SIZE + (direction.dy < 0 ? TILE_SIZE : 0) + direction.dy * (TILE_SIZE * 0.6));
        arrow.setAttribute("stroke", "red");
        arrow.setAttribute("stroke-width", "2");
        arrow.setAttribute("marker-end", "url(#arrowhead)");
        svgElement.appendChild(arrow);
    }
}




// Map color to aisle ID (adjust based on your color encoding)
function getAisleIdFromColor(r, g, b) {
    if (r === g && r === b && r < 255) return r;
    return null;
}

// Event listener for clicking on tiles
document.getElementById("mapContainer").addEventListener("click", (event) => {
    const rect = event.target.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / TILE_SIZE);
    const y = Math.floor((event.clientY - rect.top) / TILE_SIZE);

    const tile = tileMap[y] && tileMap[y][x];
    if (tile) {
        showBarcodeForm(event.clientX, event.clientY, tile.aisleId, tile.segmentId);
    }
});

// Show barcode input form at click location
function showBarcodeForm(x, y, aisleId, segmentId) {
    const form = document.getElementById("inputForm");
    form.style.left = `${x + 10}px`;
    form.style.top = `${y + 10}px`;
    form.style.display = "block";
    form.dataset.aisleId = aisleId;
    form.dataset.segmentId = segmentId;
}

// Close the form
function closeForm() {
    document.getElementById("inputForm").style.display = "none";
}

// Submit the barcode and save to the database
function submitBarcode() {
    const form = document.getElementById("inputForm");
    const barcode = document.getElementById("barcode").value;
    const aisleId = parseInt(form.dataset.aisleId);
    const segmentId = form.dataset.segmentId;

    if (barcode && aisleId && segmentId) {
        const stmt = db.prepare("INSERT INTO items (barcode, aisleId, segmentId) VALUES (?, ?, ?)");
        stmt.run([barcode, aisleId, segmentId]);
        stmt.free();
        form.style.display = "none";
        alert("Barcode saved.");
    }
}

// Initialize database on page load
window.onload = initDatabase;






// Helper function to check if a tile is walkable
function isWalkable(x, y) {
    return tileMap[y] && tileMap[y][x] === null; // null = unoccupied tile
}

// Check if tile is an aisle with an item to pick up
function isAisleWithItem(x, y, itemsToCollect) {
    // check contain aisle id in list
    const container = tileMap[y] && tileMap[y][x] !== null && itemsToCollect.includes(tileMap[y][x].aisleId);
    if (!container) return false;

    // check reachable from walkable tile
    for (const neighbor of getNeighbors({ x: x, y: y }, false)) {
        if (tileMap[neighbor.y] && tileMap[neighbor.y][neighbor.x] === null) {
            return true;
        }
    }
    return false;
}

// A* Search to find path between two points
function aStarSearch(start, goal, oneWayPassages) {
    const openSet = new Set();
    const closedSet = new Set();
    const cameFrom = {};
    const gScore = {};
    const fScore = {};

    const startKey = `${start.x},${start.y}`;
    gScore[startKey] = 0;
    fScore[startKey] = heuristic(start, goal);

    openSet.add(startKey);

    while (openSet.size > 0) {
        // Get node in openSet with lowest fScore
        let currentKey = [...openSet].reduce((lowest, nodeKey) => {
            return fScore[nodeKey] < fScore[lowest] ? nodeKey : lowest;
        });
        const [cx, cy] = currentKey.split(',').map(Number);
        const current = { x: cx, y: cy };

        // If reachable goal, reconstruct path
        for (const neighbor of getNeighbors(current, false)) {
            if (neighbor.x === goal.x && neighbor.y === goal.y) {
                return reconstructPath(cameFrom, currentKey);
            }
        }
        /*if (current.x === goal.x && current.y === goal.y) {
            return reconstructPath(cameFrom, currentKey);
        }*/

        openSet.delete(currentKey);
        closedSet.add(currentKey);

        for (const neighbor of getNeighbors(current, true)) {
            const neighborKey = `${neighbor.x},${neighbor.y}`;

            // Skip this neighbor if already evaluated
            if (closedSet.has(neighborKey)) continue;

            const tentativeGScore = gScore[currentKey] + 1;

            if (tentativeGScore < (gScore[neighborKey] || Infinity)) {
                cameFrom[neighborKey] = currentKey;
                gScore[neighborKey] = tentativeGScore;
                fScore[neighborKey] = gScore[neighborKey] + heuristic(neighbor, goal);

                if (!openSet.has(neighborKey)) openSet.add(neighborKey);
            }
        }
    }

    // Return empty path if no path found
    return [];
}

// Heuristic: grid
function heuristic(pointA, pointB) {
    //Manhattan distance
    return Math.abs(pointA.x - pointB.x) + Math.abs(pointA.y - pointB.y);
    // Euclid Distance
    return (pointA.x - pointB.x) * (pointA.x - pointB.x) + (pointA.y - pointB.y) * (pointA.y - pointB.y);
}

// Get neighboring tiles that are walkable
function getNeighbors({ x, y }, walk) {
    const directions = [
        { dx: 0, dy: -1 }, // Up
        { dx: 1, dy: 0 },  // Right
        { dx: 0, dy: 1 },  // Down
        { dx: -1, dy: 0 },  // Left
        /* { dx: 1, dy: -1 }, 
         { dx: 1, dy: 1 }, 
         { dx: -1, dy: -1 }, 
         { dx: -1, dy: 1 }*/
    ];
    const tiles = directions.map(({ dx, dy }) => ({ x: x + dx, y: y + dy }));

    if (walk) {
        return tiles.filter(({ x: nx, y: ny }) => {
            if (!isWalkable(nx, ny)) return false;

            const neighborTileKey = `${nx},${ny}`;
            // Check if the neighbor tile itself has a one-way restriction for incoming movement
            if (oneWayPassages[neighborTileKey]) {
                const { dx: allowedDx, dy: allowedDy } = oneWayPassages[neighborTileKey];
                const direction = { dx: nx - x, dy: ny - y };

                // If returning to the current tile violates the neighbor's one-way rule, skip it
                if (direction.dx !== allowedDx || direction.dy !== allowedDy) {
                    return false;
                }
            }
            return true;
        });
    }
    return tiles;
}

// Reconstruct the path from A* search
function reconstructPath(cameFrom, currentKey) {
    const path = [];
    while (cameFrom[currentKey]) {
        const [x, y] = currentKey.split(',').map(Number);
        path.unshift({ x, y });
        currentKey = cameFrom[currentKey];
    }
    return path;
}

// Find closest item to current position
function findClosestItem(currentPos, itemsToCollect) {
    let minDistance = Infinity;
    let closestItemPos = null;

    for (let y = 0; y < TILE_MAP_HEIGHT; y++) {
        for (let x = 0; x < TILE_MAP_WIDTH; x++) {
            if (isAisleWithItem(x, y, itemsToCollect)) {
                const distance = heuristic(currentPos, { x, y });
                if (distance < minDistance) {
                    minDistance = distance;
                    closestItemPos = { x, y, aisleId: tileMap[y][x].aisleId };
                }
            }
        }
    }
    console.log(closestItemPos);
    return closestItemPos;
}

// Main function to collect items in order and reach endpoint
function findPathWithItems() {
    let currentPos = entryPoint;
    const path = [];
    const itemsToCollect = [...itemList]; // Clone item list to track remaining items

    // Collect each item in the closest order
    while (itemsToCollect.length > 0) {
        const closestItem = findClosestItem(currentPos, itemsToCollect);
        if (!closestItem) {
            console.log("No path to remaining items.");
            return [];
        }

        const itemPath = aStarSearch(currentPos, closestItem);
        if (itemPath.length === 0) {
            console.log("No path found to item at:", closestItem);
            return [];
        }

        path.push(...itemPath);
        currentPos = path.at(-1);
        itemsToCollect.splice(itemsToCollect.indexOf(closestItem.aisleId), 1);
    }

    // After collecting all items, path to the endpoint
    const exitPath = aStarSearch(currentPos, endPoint);
    if (exitPath.length === 0) {
        console.log("No path found to endpoint.");
        return [];
    }
    path.push(...exitPath);

    return path;
}


// Function to draw the path in the SVG map
function drawPath(svgElement, path) {
    // Create a polyline element for the path
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");

    // Generate the points attribute for polyline
    const points = path.map(point => `${(point.x) * TILE_SIZE + TILE_SIZE * 0.5},${(point.y) * TILE_SIZE + TILE_SIZE * 0.5}`).join(" ");

    // Set the points attribute for the polyline
    polyline.setAttribute("points", points);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", "red");
    polyline.setAttribute("stroke-width", "2");

    // Add the polyline to the SVG element
    svgElement.appendChild(polyline);
}



const shortestPaths = {}; // Format: { "aisleA_aisleB": { path: [...], distance: X } }

function runAStarForAisles(allAisles) {
    allAisles.forEach((aisleA, indexA) => {
        allAisles.forEach((aisleB, indexB) => {
            if (indexA === indexB) return; // Skip self-pairs

            const result = aStar(aisleA, aisleB); // Run A* from aisleA to aisleB
            shortestPaths[`${aisleA.id}_${aisleB.id}`] = { path: result.path, distance: result.distance };
        });
    });
}


for 