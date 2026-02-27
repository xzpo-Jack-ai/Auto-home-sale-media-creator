-- CreateTable
CREATE TABLE "hot_trends" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "city" TEXT NOT NULL,
    "keyword" TEXT NOT NULL,
    "heat" INTEGER NOT NULL,
    "rank" INTEGER NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'douyin',
    "fetchedAt" DATETIME NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateIndex
CREATE UNIQUE INDEX "hot_trends_city_keyword_fetchedAt_key" ON "hot_trends"("city", "keyword", "fetchedAt");

-- CreateIndex
CREATE INDEX "hot_trends_city_heat_idx" ON "hot_trends"("city", "heat");

-- CreateIndex
CREATE INDEX "hot_trends_fetchedAt_idx" ON "hot_trends"("fetchedAt");
