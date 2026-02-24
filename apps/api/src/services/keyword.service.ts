import { prisma } from '../lib/prisma';

export interface KeywordData {
  city: string;
  text: string;
  heat?: number;
}

export interface KeywordWithStats {
  id: string;
  text: string;
  heat: number;
}

export class KeywordDAO {
  /**
   * 获取城市的热词列表
   */
  static async getByCity(city: string): Promise<KeywordWithStats[]> {
    const keywords = await prisma.keyword.findMany({
      where: { city },
      orderBy: { heat: 'desc' },
      take: 10,
    });

    return keywords.map((k) => ({
      id: k.id,
      text: k.text,
      heat: k.heat,
    }));
  }

  /**
   * 批量插入或更新热词
   */
  static async upsertMany(data: KeywordData[]) {
    const operations = data.map((item) =>
      prisma.keyword.upsert({
        where: {
          city_text: {
            city: item.city,
            text: item.text,
          },
        },
        update: {
          heat: item.heat ?? Math.floor(Math.random() * 50) + 50,
        },
        create: {
          city: item.city,
          text: item.text,
          heat: item.heat ?? Math.floor(Math.random() * 50) + 50,
        },
      })
    );

    return prisma.$transaction(operations);
  }

  /**
   * 获取所有城市列表
   */
  static async getCities(): Promise<string[]> {
    const result = await prisma.keyword.groupBy({
      by: ['city'],
    });
    return result.map((r) => r.city);
  }
}
