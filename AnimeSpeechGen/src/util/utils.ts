import { pa } from "element-plus/es/locales.mjs";

// 获取assets静态资源
export const getAssetsFile = (url: string) => {
  return new URL(`@/assets/images/${url}`, import.meta.url).href;
};

export const getLiHuiAssetsFile = (belong: string, url: string) => {
  return new URL(`@/assets/LiHui/${belong}/${url}`, import.meta.url).href;
};

// export function loadAnimeStandImages(folder: null | string = null, type: string = "png") {
//   // 使用 import.meta.glob 来动态获取指定文件夹下的所有文件
//   const direction: string = folder ? `@/assets/LiHui/${folder}/*.${type}`: `@/assets/Lihui/*.${type}`;
//   const images = import.meta.glob(direction);

//   // 返回所有符合条件的图片 URL
//   const imageUrls = Object.keys(images).map((key) => {
//     // 使用 URL() 方法将相对路径转换为可用的 URL
//     return new URL(key, import.meta.url).href;
//   });

//   return imageUrls;
// }


// 随机生成字符串
export const generateRandomString = (length: any) => {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  const charactersLength = characters.length;

  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }

  return result;
}
