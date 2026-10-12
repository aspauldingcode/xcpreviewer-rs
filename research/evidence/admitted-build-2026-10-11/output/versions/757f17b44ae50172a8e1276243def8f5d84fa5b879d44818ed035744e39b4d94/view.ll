; ModuleID = 'literal-view.c'
source_filename = "literal-view.c"
target datalayout = "e-m:e-p:32:32-p10:8:8-p20:8:8-i64:64-i128:128-n32:64-S128-ni:1:10:20"
target triple = "wasm32"

@buffer = internal global [16384 x i8] zeroinitializer, align 16

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define hidden noundef nonnull ptr @pixels() local_unnamed_addr #0 {
  ret ptr @buffer
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define hidden noundef i32 @capacity() local_unnamed_addr #0 {
  ret i32 16384
}

; Function Attrs: nofree norecurse nosync nounwind memory(write, argmem: none, inaccessiblemem: none)
define hidden range(i32 0, 2305) i32 @render(i32 noundef %0) local_unnamed_addr #1 {
  %2 = add i32 %0, -257
  %3 = icmp ult i32 %2, -189
  br i1 %3, label %73, label %4

4:                                                ; preds = %1
  %5 = icmp samesign ugt i32 %0, 68
  %6 = add nsw i32 %0, -69
  %7 = and i32 %0, 3
  %8 = icmp ult i32 %6, 3
  %9 = and i32 %0, 508
  %10 = add nsw i32 %9, -72
  %11 = icmp eq i32 %7, 0
  br label %12

12:                                               ; preds = %53, %4
  %13 = phi i32 [ 0, %4 ], [ %54, %53 ]
  %14 = mul nuw nsw i32 %13, %0
  br label %19

15:                                               ; preds = %53
  %16 = mul nuw nsw i32 %0, 9
  br label %73

17:                                               ; preds = %19
  br i1 %5, label %18, label %53

18:                                               ; preds = %17
  br i1 %8, label %43, label %56

19:                                               ; preds = %31, %12
  %20 = phi i32 [ 0, %12 ], [ %42, %31 ]
  %21 = shl nuw nsw i32 %20, 2
  %22 = add nuw nsw i32 %21, %14
  %23 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %22
  store i8 60, ptr %23, align 1, !tbaa !2
  %24 = add nuw nsw i32 %22, 1
  %25 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %24
  store i8 96, ptr %25, align 1, !tbaa !2
  %26 = add nuw nsw i32 %22, 2
  %27 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %26
  store i8 99, ptr %27, align 1, !tbaa !2
  %28 = add nuw nsw i32 %22, 3
  %29 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %28
  store i8 -1, ptr %29, align 1, !tbaa !2
  %30 = icmp eq i32 %20, 16
  br i1 %30, label %17, label %31, !llvm.loop !5

31:                                               ; preds = %19
  %32 = shl i32 %20, 2
  %33 = or disjoint i32 %32, 4
  %34 = add nuw nsw i32 %33, %14
  %35 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %34
  store i8 60, ptr %35, align 1, !tbaa !2
  %36 = add nuw nsw i32 %34, 1
  %37 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %36
  store i8 96, ptr %37, align 1, !tbaa !2
  %38 = add nuw nsw i32 %34, 2
  %39 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %38
  store i8 99, ptr %39, align 1, !tbaa !2
  %40 = add nuw nsw i32 %34, 3
  %41 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %40
  store i8 -1, ptr %41, align 1, !tbaa !2
  %42 = add nuw nsw i32 %20, 2
  br label %19

43:                                               ; preds = %56, %18
  %44 = phi i32 [ 68, %18 ], [ %70, %56 ]
  br i1 %11, label %53, label %45

45:                                               ; preds = %43, %45
  %46 = phi i32 [ %50, %45 ], [ %44, %43 ]
  %47 = phi i32 [ %51, %45 ], [ 0, %43 ]
  %48 = add nuw nsw i32 %46, %14
  %49 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %48
  store i8 -91, ptr %49, align 1, !tbaa !2
  %50 = add nuw nsw i32 %46, 1
  %51 = add i32 %47, 1
  %52 = icmp eq i32 %51, %7
  br i1 %52, label %53, label %45, !llvm.loop !7

53:                                               ; preds = %43, %45, %17
  %54 = add nuw nsw i32 %13, 1
  %55 = icmp eq i32 %54, 9
  br i1 %55, label %15, label %12, !llvm.loop !9

56:                                               ; preds = %18, %56
  %57 = phi i32 [ %70, %56 ], [ 68, %18 ]
  %58 = phi i32 [ %71, %56 ], [ 0, %18 ]
  %59 = add nuw nsw i32 %57, %14
  %60 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %59
  store i8 -91, ptr %60, align 1, !tbaa !2
  %61 = or disjoint i32 %57, 1
  %62 = add nuw nsw i32 %61, %14
  %63 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %62
  store i8 -91, ptr %63, align 1, !tbaa !2
  %64 = or disjoint i32 %57, 2
  %65 = add nuw nsw i32 %64, %14
  %66 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %65
  store i8 -91, ptr %66, align 1, !tbaa !2
  %67 = or disjoint i32 %57, 3
  %68 = add nuw nsw i32 %67, %14
  %69 = getelementptr inbounds nuw [16384 x i8], ptr @buffer, i32 0, i32 %68
  store i8 -91, ptr %69, align 1, !tbaa !2
  %70 = add nuw nsw i32 %57, 4
  %71 = add i32 %58, 4
  %72 = icmp eq i32 %58, %10
  br i1 %72, label %43, label %56, !llvm.loop !10

73:                                               ; preds = %1, %15
  %74 = phi i32 [ %16, %15 ], [ 0, %1 ]
  ret i32 %74
}

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) "no-builtins" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+bulk-memory,+bulk-memory-opt,+call-indirect-overlong,+multivalue,+mutable-globals,+nontrapping-fptoint,+reference-types,+sign-ext" }
attributes #1 = { nofree norecurse nosync nounwind memory(write, argmem: none, inaccessiblemem: none) "no-builtins" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+bulk-memory,+bulk-memory-opt,+call-indirect-overlong,+multivalue,+mutable-globals,+nontrapping-fptoint,+reference-types,+sign-ext" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"Apple clang version 21.0.0 (https://github.com/swiftlang/llvm-project.git b6f042d4515f83404d3f44012144b5e67b2c5791)"}
!2 = !{!3, !3, i64 0}
!3 = !{!"omnipotent char", !4, i64 0}
!4 = !{!"Simple C/C++ TBAA"}
!5 = distinct !{!5, !6}
!6 = !{!"llvm.loop.mustprogress"}
!7 = distinct !{!7, !8}
!8 = !{!"llvm.loop.unroll.disable"}
!9 = distinct !{!9, !6}
!10 = distinct !{!10, !6}
