/**
 * 生成字符串的简单哈希值
 * @param {string} str - 要哈希的字符串
 * @returns {string} 哈希字符串
 */
export function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // 转换为32位整数
  }
  return Math.abs(hash).toString(36); // 转换为36进制字符串
}