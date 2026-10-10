package io.github.aemiroo.yetiboss;
import java.util.*;
final class FrostRules {
    static final Set<String> SPECIAL=Set.of("frostfang","frostbow","frostpickaxe");
    static boolean allowed(String kind,String enchant) {
        if(Set.of("unbreaking","mending").contains(enchant))return true;
        return switch(kind) {
            case "frostfang" -> Set.of("sharpness","looting").contains(enchant);
            case "frostbow" -> enchant.equals("power");
            case "frostpickaxe" -> Set.of("efficiency","fortune","silk_touch").contains(enchant);
            default -> false;
        };
    }
    static boolean compatible(String kind,Set<String> enchants) {
        return enchants.stream().allMatch(e->allowed(kind,e))&&!(enchants.contains("fortune")&&enchants.contains("silk_touch"))
            &&!(enchants.contains("infinity")&&enchants.contains("mending"));
    }
    static int combine(int a,int b){return Math.min(3,a==b?a+1:Math.max(a,b));}
    static int amount(Random random,int min,int max){return min+random.nextInt(max-min+1);}
}
