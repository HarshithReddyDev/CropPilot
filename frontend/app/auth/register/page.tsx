"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Loader2, Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthLayout } from "@/components/shared/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { INDIAN_STATES } from "@/lib/constants";
import { useAuth } from "@/hooks/use-auth";

const districtsByState: Record<string, string[]> = {
  "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Aurangabad", "Solapur", "Kolhapur"],
  "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj", "Gorakhpur", "Meerut", "Bareilly"],
  "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali", "Hoshiarpur"],
  "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala", "Karnal", "Rohtak", "Hisar"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli"],
  "Karnataka": ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi", "Davanagere"],
  "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar"],
  "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer"],
  "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga", "Purnia"],
  "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar"],
  "West Bengal": ["Kolkata", "Howrah", "Darjeeling", "Siliguri", "Bardhaman", "Nadia"],
  "Delhi": ["New Delhi", "Central Delhi", "South Delhi", "North Delhi", "East Delhi", "West Delhi"],
};

const registerSchema = z
  .object({
    fullName: z.string().min(2, "Full name must be at least 2 characters"),
    email: z.string().min(1, "Email is required").email("Invalid email address"),
    phone: z
      .string()
      .min(10, "Phone number must be at least 10 digits")
      .max(15, "Phone number too long")
      .regex(/^\+?[\d\s-]+$/, "Invalid phone number"),
    state: z.string().min(1, "Please select a state"),
    district: z.string().min(1, "Please select a district"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
    acceptTerms: z.boolean().refine((v) => v === true, {
      message: "You must accept the terms and conditions",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      fullName: "",
      email: "",
      phone: "",
      state: "",
      district: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false as unknown as true,
    },
  });

  const stateValue = watch("state");
  const districts = stateValue ? districtsByState[stateValue] ?? [] : [];

  const onSubmit = async (data: RegisterForm) => {
    setError(null);
    try {
      await registerUser.mutateAsync({
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        phone: data.phone,
        role: "farmer",
        state: data.state,
        district: data.district,
      });
      router.push("/dashboard");
    } catch (e: unknown) {
      const message =
        e instanceof Error ? e.message : "Registration failed. Please try again.";
      setError(message);
    }
  };

  return (
    <AuthLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h1 className="text-2xl font-bold text-foreground">Create Account</h1>
        <p className="mt-1 text-sm text-muted-foreground">Join CropPilot and start your smart farming journey</p>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                placeholder="Harsh Raj"
                {...register("fullName")}
                className={errors.fullName ? "border-destructive" : ""}
              />
              {errors.fullName && (
                <p className="text-xs text-destructive">{errors.fullName.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+91 98765 43210"
                {...register("phone")}
                className={errors.phone ? "border-destructive" : ""}
              />
              {errors.phone && (
                <p className="text-xs text-destructive">{errors.phone.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="farmer@example.com"
              {...register("email")}
              className={errors.email ? "border-destructive" : ""}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="state">State</Label>
              <Select
                value={watch("state")}
                onValueChange={(v) => {
                  setValue("state", v, { shouldValidate: true });
                  setValue("district", "", { shouldValidate: true });
                }}
              >
                <SelectTrigger className={errors.state ? "border-destructive" : ""}>
                  <SelectValue placeholder="Select state" />
                </SelectTrigger>
                <SelectContent>
                  {INDIAN_STATES.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.state && (
                <p className="text-xs text-destructive">{errors.state.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="district">District</Label>
              <Select
                value={watch("district")}
                disabled={!stateValue}
                onValueChange={(v) => setValue("district", v, { shouldValidate: true })}
              >
                <SelectTrigger className={errors.district ? "border-destructive" : ""}>
                  <SelectValue placeholder={stateValue ? "Select district" : "Select state first"} />
                </SelectTrigger>
                <SelectContent>
                  {districts.map((d) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.district && (
                <p className="text-xs text-destructive">{errors.district.message}</p>
              )}
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a password"
                  {...register("password")}
                  className={errors.password ? "border-destructive pr-10" : "pr-10"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-destructive">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm your password"
                  {...register("confirmPassword")}
                  className={errors.confirmPassword ? "border-destructive pr-10" : "pr-10"}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>
              )}
            </div>
          </div>

          <div className="flex items-start gap-2">
            <Checkbox
              id="acceptTerms"
              className="mt-0.5"
              onCheckedChange={(v) => setValue("acceptTerms", v === true as unknown as true, { shouldValidate: true })}
            />
            <Label htmlFor="acceptTerms" className="text-sm font-normal text-muted-foreground cursor-pointer leading-relaxed">
              I accept the{" "}
              <Link href="/terms" className="font-medium text-primary hover:text-primary/80">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="/privacy" className="font-medium text-primary hover:text-primary/80">
                Privacy Policy
              </Link>
            </Label>
          </div>
          {errors.acceptTerms && (
            <p className="text-xs text-destructive">{errors.acceptTerms.message}</p>
          )}

          <Button type="submit" className="w-full gap-2" disabled={registerUser.isPending}>
            {registerUser.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating account...
              </>
            ) : (
              "Create Account"
            )}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/auth/login" className="font-medium text-primary hover:text-primary/80 transition-colors">
            Sign in
          </Link>
        </p>
      </motion.div>
    </AuthLayout>
  );
}
