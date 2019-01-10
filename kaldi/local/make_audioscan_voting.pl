#!/usr/bin/perl
# prepare data (RealWorld associatation result) for fine-tuning 

if (@ARGV != 2) {
  print STDERR "Usage: $0 <path-to-audioscanvoting> <path-to-data-dir>\n";
  print STDERR "e.g. $0 /export/audioscan_voting data/audioscan_voting\n";
  exit(1);
}


($data_base, $out_dir) = @ARGV;

opendir my $dh, "$data_base" or die "Cannot open directory: $!";
my @spkr_dirs = grep {-d "$data_base/$_" && ! /^\.{1,2}$/} readdir($dh);
closedir $dh;

if (! -d "$out_dir") {
  mkdir($out_dir) or die "Could not create directory $!";
}
open(SPKR, ">", "$out_dir/utt2spk") or die "Could not open the output file $out_dir/utt2spk";
open(WAV, ">", "$out_dir/wav.scp") or die "Could not open the output file $out_dir/wav.scp";

foreach (@spkr_dirs) {
  my $spkr_id = $_;
  opendir my $dh, "$data_base/$spkr_id/" or die "Cannot open directory: $!";
  my @files = map{s/\.[^.]+$//;$_}grep {/\.wav$/} readdir($dh);
  closedir $dh;

  foreach (@files) {
    my $name = $_;
    my $wav = "$data_base/$spkr_id/$name.wav";
    my $utt_id = "$spkr_id-$name";
    print WAV "$utt_id", " $wav", "\n";
    print SPKR "$utt_id", " $spkr_id", "\n";
  }
}

close(SPKR) or die;
close(WAV) or die;

if (system(
  "utils/utt2spk_to_spk2utt.pl $out_dir/utt2spk >$out_dir/spk2utt") != 0) {
  die "Error creating spk2utt file in directory $out_dir";
}
system("env LC_COLLATE=C utils/fix_data_dir.sh $out_dir");
if (system("env LC_COLLATE=C utils/validate_data_dir.sh --no-text --no-feats $out_dir") != 0) {
  die "Error validating directory $out_dir";
}

